# SPDX-License-Identifier: LGPL-3.0-only
"""NHTSA recall feed client.

NHTSA's Recalls API is public, free, JSON over HTTPS, no auth.
Endpoint: https://api.nhtsa.gov/recalls/recallsByVehicle
Parameters: make, model, modelYear

The advisory rate limit is 1 request per second. We respect it with an
explicit sleep between calls. The daily cron is forgiving of this — a
typical AlfaCore fleet of a few hundred vehicles dedupes to maybe
10-20 unique (make, model, year) tuples, well under the 1/sec budget.

Pattern 10 — honest boundaries. HTTP failures are logged and skipped;
we never crash the cron, never partial-commit a campaign in a broken state.
If the NHTSA API returns a malformed record, that record is skipped and
logged; sibling records still process.
"""

import json
import logging
import time
from datetime import datetime

from odoo import api, models

_logger = logging.getLogger(__name__)

NHTSA_BASE_URL = "https://api.nhtsa.gov"
NHTSA_RECALLS_ENDPOINT = "/recalls/recallsByVehicle"

# NHTSA returns dates as "DD/MM/YYYY" — quirky but consistent.
NHTSA_DATE_FORMAT = "%d/%m/%Y"

# Rate limit: NHTSA advises 1 req/sec. We sleep this long between calls.
NHTSA_RATE_LIMIT_SECONDS = 1.1

# Per-call HTTP settings
HTTP_CONNECT_TIMEOUT = 10.0
HTTP_READ_TIMEOUT = 30.0
HTTP_MAX_RETRIES = 3
HTTP_RETRY_BACKOFF_BASE = 2.0  # 2s, 4s, 8s


class AlfaNhtsaClient(models.AbstractModel):
    _name = "alfa_core_campaign.nhtsa_client"
    _description = "NHTSA Recall Client"

    # ------------------------------------------------------------------------
    # Cron entry — orchestrates the full poll
    # ------------------------------------------------------------------------
    @api.model
    def poll_nhtsa(self):
        """Iterate fleet (make, model, year) tuples, fetch recalls, upsert
        campaigns, then run targeting on newly-imported campaigns.

        Returns a summary dict with counts. Logs at info level throughout
        so the cron run is readable in the Odoo log.
        """
        Vehicle = self.env["alfa_fleet.vehicle"]
        Campaign = self.env["alfa_core_campaign.campaign"].sudo()

        # Read-group the fleet so we make at most one HTTP call per unique
        # (make, model, year) tuple, regardless of how many vehicles share it.
        groups = Vehicle.read_group(
            domain=[("state", "in", ("active", "in_service"))],
            fields=["make", "model", "year"],
            groupby=["make", "model", "year"],
            lazy=False,
        )

        summary = {
            "tuples_queried": 0,
            "tuples_failed": 0,
            "campaigns_imported": 0,
            "campaigns_updated": 0,
            "campaigns_targeted": 0,
        }

        for grp in groups:
            make = grp.get("make")
            model = grp.get("model")
            year = grp.get("year")
            if not (make and model and year):
                continue

            try:
                recalls = self._fetch_nhtsa_recalls(make, model, year)
                summary["tuples_queried"] += 1
            except Exception as e:
                _logger.warning(
                    "NHTSA fetch failed for (%s, %s, %s): %s. Skipping.",
                    make,
                    model,
                    year,
                    e,
                )
                summary["tuples_failed"] += 1
                continue

            for record in recalls:
                try:
                    campaign, is_new = self.upsert_campaign_from_nhtsa_record(record)
                    if campaign:
                        if is_new:
                            summary["campaigns_imported"] += 1
                        else:
                            summary["campaigns_updated"] += 1
                except Exception as e:
                    _logger.warning(
                        "NHTSA upsert failed for %s: %s. Skipping record.",
                        record.get("NHTSACampaignNumber", "?"),
                        e,
                    )

            # Rate limit between fleet tuples
            time.sleep(NHTSA_RATE_LIMIT_SECONDS)

        # After ingestion, target affected vehicles for any newly-imported
        # campaigns. action_target_vehicles is idempotent — re-running on
        # a campaign that's already targeted creates no duplicate targets.
        new_campaigns = Campaign.search([("state", "=", "imported")])
        if new_campaigns:
            new_campaigns.action_target_vehicles()
            summary["campaigns_targeted"] = len(new_campaigns)

        _logger.info("NHTSA poll complete: %s", summary)
        return summary

    # ------------------------------------------------------------------------
    # Single HTTP call with retries
    # ------------------------------------------------------------------------
    @api.model
    def _fetch_nhtsa_recalls(self, make, model, year):
        """GET /recalls/recallsByVehicle?make={make}&model={model}&modelYear={year}.

        Returns a list of recall records (possibly empty). Raises only on
        unrecoverable errors after exhausting retries — caller is expected
        to catch and log.
        """
        # Imported here so unit tests can patch requests without crashing
        # the module load on environments without requests installed.
        import requests

        url = f"{NHTSA_BASE_URL}{NHTSA_RECALLS_ENDPOINT}"
        params = {
            "make": str(make).strip(),
            "model": str(model).strip(),
            "modelYear": int(year),
        }

        last_exception = None
        for attempt in range(HTTP_MAX_RETRIES):
            try:
                response = requests.get(
                    url,
                    params=params,
                    timeout=(HTTP_CONNECT_TIMEOUT, HTTP_READ_TIMEOUT),
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "AlfaCore/1.0 (https://odooiq.com)",
                    },
                )
                response.raise_for_status()
                payload = response.json()
                # NHTSA returns {"Count": N, "Message": "...", "results": [...]}
                # Be defensive: accept either "results" or "Results"
                results = payload.get("results") or payload.get("Results") or []
                if not isinstance(results, list):
                    _logger.warning(
                        "NHTSA returned non-list results for (%s, %s, %s): %s",
                        make,
                        model,
                        year,
                        type(results).__name__,
                    )
                    return []
                return results

            except requests.exceptions.HTTPError as e:
                # 4xx errors are not worth retrying — likely a bad request
                if e.response is not None and 400 <= e.response.status_code < 500:
                    _logger.info(
                        "NHTSA 4xx for (%s, %s, %s): %d. Not retrying.",
                        make,
                        model,
                        year,
                        e.response.status_code,
                    )
                    return []
                last_exception = e
            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                json.JSONDecodeError,
            ) as e:
                # HTTPError already handled above (4xx returns []; 5xx falls
                # through to retry by setting last_exception). Including it
                # in this tuple would be unreachable.
                last_exception = e

            # Backoff before retrying
            if attempt < HTTP_MAX_RETRIES - 1:
                backoff = HTTP_RETRY_BACKOFF_BASE ** (attempt + 1)
                _logger.info(
                    "NHTSA fetch attempt %d/%d failed (%s). Retrying in %.1fs.",
                    attempt + 1,
                    HTTP_MAX_RETRIES,
                    last_exception,
                    backoff,
                )
                time.sleep(backoff)

        # Exhausted retries
        raise last_exception or RuntimeError("NHTSA fetch failed for unknown reason")

    # ------------------------------------------------------------------------
    # Idempotent upsert
    # ------------------------------------------------------------------------
    @api.model
    def upsert_campaign_from_nhtsa_record(self, nhtsa_record):
        """Given a NHTSA JSON record, upsert a campaign.

        Returns (campaign_recordset, is_new: bool).

        NHTSA record fields (per current API documentation):
          NHTSACampaignNumber    e.g. "23V456000"
          Manufacturer           e.g. "FCA US LLC"
          ReportReceivedDate     e.g. "23/06/2023" (DD/MM/YYYY)
          Component              e.g. "FUEL SYSTEM, GASOLINE"
          Summary                customer-facing risk explanation
          Consequence            sometimes used instead of Summary
          Remedy                 dealer action
          parkIt                 bool — do-not-drive recall
          parkOutSide            bool — fire risk, park outdoors
          overTheAirUpdate       bool — OTA remediable
        """
        source_id = nhtsa_record.get("NHTSACampaignNumber")
        if not source_id:
            return self.env["alfa_core_campaign.campaign"].browse(), False

        Campaign = self.env["alfa_core_campaign.campaign"].sudo()
        existing = Campaign.search(
            [
                ("source", "=", "nhtsa"),
                ("source_id", "=", source_id),
            ],
            limit=1,
        )

        # Map NHTSA severity-adjacent flags onto our internal severity enum.
        # parkIt = do-not-drive = safety_critical
        # parkOutSide = fire/explosion risk = safety_critical
        # otherwise default to 'high' for safety recalls (NHTSA Recalls API
        # only returns safety recalls and emissions, not service campaigns)
        severity = "high"
        if nhtsa_record.get("parkIt") or nhtsa_record.get("parkOutSide"):
            severity = "safety_critical"

        # Combine Summary + Consequence into our risk_summary
        risk_parts = []
        if nhtsa_record.get("Summary"):
            risk_parts.append(nhtsa_record["Summary"].strip())
        if nhtsa_record.get("Consequence") and nhtsa_record["Consequence"] != nhtsa_record.get(
            "Summary"
        ):
            risk_parts.append("Consequence: " + nhtsa_record["Consequence"].strip())
        risk_summary = "\n\n".join(risk_parts) if risk_parts else False

        # Append the special flags to the remedy text so they're visible
        remedy = (nhtsa_record.get("Remedy") or "").strip()
        flags = []
        if nhtsa_record.get("parkIt"):
            flags.append("PARK IT — do not drive until remedied")
        if nhtsa_record.get("parkOutSide"):
            flags.append("PARK OUTSIDE — fire/explosion risk")
        if nhtsa_record.get("overTheAirUpdate"):
            flags.append("OTA remediable — may not require dealer visit")
        if flags:
            remedy = "\n\n".join(flags) + ("\n\n" + remedy if remedy else "")

        vals = {
            "source": "nhtsa",
            "source_id": source_id,
            "manufacturer": nhtsa_record.get("Manufacturer") or "Unknown",
            "affected_components": (nhtsa_record.get("Component") or "")[:255],
            "risk_summary": risk_summary,
            "remedy_summary": remedy or False,
            "campaign_type": "safety_recall",
            "severity": severity,
        }

        # Parse issued_date if present
        date_str = nhtsa_record.get("ReportReceivedDate")
        if date_str:
            try:
                vals["issued_date"] = datetime.strptime(date_str, NHTSA_DATE_FORMAT).date()
            except ValueError:
                # Some records may use a different format; skip silently
                pass

        if existing:
            existing.write(vals)
            return existing, False

        # New campaign — synthesize a reasonable display name
        component = (nhtsa_record.get("Component") or "").split(",")[0].strip()
        manufacturer = nhtsa_record.get("Manufacturer", "").strip()
        vals["name"] = (
            f"{manufacturer}: {component}"
            if manufacturer and component
            else (nhtsa_record.get("Summary") or source_id)
        )[:200]
        vals["state"] = "imported"
        return Campaign.create(vals), True
