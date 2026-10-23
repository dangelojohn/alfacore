# SPDX-License-Identifier: LGPL-3.0-only
"""One row per imported CUORE bundle, and the single service method that imports it.

The bundle is untrusted input (integration spec 3 and 6.4): it is validated by the
vendored, dependency-free ``lib.bundle_schema`` before anything is read, mapped only
onto models and fields that exist, and written inside one savepoint so a failure
leaves AlfaCore unchanged.

Twelve Patterns honoured here:
  1. state machine validated -> imported / failed / superseded, every step on the chatter
  2. fail loud: a VIN mismatch, unknown vehicle or tampered file is refused with a reason
  4. per-record isolation: everything created is anchored to one vehicle by VIN
  5. idempotent: ``bundle_uuid`` is unique; re-import is a no-op
  8. information budget: JSON blobs are capped, the original zip is attached
  9. logging as UI: the validation report is on the record
 10. honest boundaries: no customers or vehicles are created, no confidence is invented
 11. ``inference_zde = True`` on every record the importer creates
"""

import base64
import json
import logging
import os
import re

from odoo import _, api, fields, models
from odoo.exceptions import AccessError

from ..lib import bundle_reader, bundle_schema
from .cuore_hypothesis import EVIDENCE_CLASSES
from .guard import MAIL_FIELDS, guard_write

_logger = logging.getLogger(__name__)

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
STATION_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")  # ISO 3779: no I, O, Q
#: Information budget (Pattern 8) for one JSON text blob stored on a row.
JSON_BUDGET = 1_000_000
DEFAULT_MAX_AGE_DAYS = 14
STEP_TEXT_KINDS = ("record", "decide")


def json_text(obj):
    """Readable JSON for a read-only text field; a marker if it exceeds the budget."""
    if obj in (None, "", [], {}):
        return False
    text = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False, default=str)
    if len(text) > JSON_BUDGET:
        return json.dumps(
            {
                "truncated": True,
                "chars": len(text),
                "note": "Too large to store inline; the full content is in the attached bundle.",
            }
        )
    return text


class AlfaCuoreBundle(models.Model):
    _name = "alfa.cuore.bundle"
    _description = "CUORE Bundle"
    _inherit = ["mail.thread"]
    _order = "imported_at desc, id desc"
    _rec_name = "name"

    name = fields.Char(required=True, copy=False, readonly=True, default=lambda s: _("New"))
    bundle_uuid = fields.Char(
        string="Bundle UUID",
        required=True,
        readonly=True,
        copy=False,
        index=True,
        help="Idempotency key. Importing the same UUID again creates nothing.",
    )
    schema_version = fields.Char(readonly=True)
    station_id = fields.Char(string="Station", readonly=True, index=True)
    kind = fields.Selection([("scan", "Scan"), ("job", "Job")], readonly=True)
    source_id = fields.Char(
        string="Source ID",
        readonly=True,
        help="scan_id (scan) or job_id (job) as CUORE knows it; unique only with the station.",
    )
    vin = fields.Char(string="VIN", size=17, readonly=True, index=True)
    vehicle_id = fields.Many2one("alfa_fleet.vehicle", readonly=True, index=True)
    sale_order_id = fields.Many2one("sale.order", string="Service Order", readonly=True, index=True)
    cuore_version = fields.Char(readonly=True)
    created_at = fields.Datetime(string="Created (UTC)", readonly=True)
    created_at_local = fields.Char(string="Created (as sent)", readonly=True)
    tz = fields.Char(string="Station Time Zone", readonly=True)
    finalized = fields.Boolean(
        readonly=True,
        help="False when a guided scan is paused or a job is open: a later bundle may supersede.",
    )
    imported_at = fields.Datetime(readonly=True)
    imported_by_id = fields.Many2one("res.users", string="Imported By", readonly=True)
    state = fields.Selection(
        [
            ("validated", "Validated"),
            ("imported", "Imported"),
            ("failed", "Failed"),
            ("superseded", "Superseded"),
        ],
        default="validated",
        required=True,
        readonly=True,
        tracking=True,
        index=True,
    )
    validation_report = fields.Text(readonly=True)
    file_sha256 = fields.Char(string="File SHA-256", readonly=True)
    filename = fields.Char(readonly=True)
    attachment_id = fields.Many2one("ir.attachment", string="Original Bundle", readonly=True)

    # Records created
    scan_session_id = fields.Many2one(
        "alfa_core_scanner.scan_session", string="Scan Session", readonly=True, ondelete="set null"
    )
    report_id = fields.Many2one(
        "alfa_core_diagnosis.report", string="Diagnosis", readonly=True, ondelete="set null"
    )
    inspection_ids = fields.Many2many(
        "alfa_core_inspection.inspection",
        "alfa_cuore_bundle_inspection_rel",
        "bundle_id",
        "inspection_id",
        string="Inspections (mechanic steps)",
        readonly=True,
    )
    hypothesis_ids = fields.One2many(
        "alfa.cuore.hypothesis", "bundle_id", string="Hypotheses", readonly=True
    )
    dtc_count = fields.Integer(string="DTC Rows", readonly=True)
    hypothesis_count = fields.Integer(readonly=True)
    step_count = fields.Integer(string="Mechanic Steps", readonly=True)

    # Read-only JSON, stored as sent (Pattern 8: capped)
    code_findings_json = fields.Text(
        string="Code Findings (JSON)",
        readonly=True,
        help="Per-code findings with readings, inference, outside literature and "
        "owner-attested statements kept apart.",
    )
    tsb_xref_json = fields.Text(
        string="TSB Cross-Reference (JSON)",
        readonly=True,
        help="Bulletin relations computed in CUORE. Suggestions, never a reading.",
    )

    _bundle_uuid_uniq = models.Constraint(
        "UNIQUE(bundle_uuid)", "This CUORE bundle UUID already exists."
    )

    # ------------------------------------------------------------------------
    # ORM
    # ------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("alfa.cuore.bundle") or _("New")
        return super().create(vals_list)

    def write(self, vals):
        guard_write(self, vals, free_fields=MAIL_FIELDS)
        return super().write(vals)

    def unlink(self):
        """Manager-only (ACL). Deleting an imported bundle removes what it created, so the
        same file can be imported again after a wrong import."""
        self.check_access("unlink")  # the elevated super() call below would skip the ACL
        for rec in self.filtered(lambda b: b.state == "imported"):
            elevated = rec.sudo().with_context(cuore_import=True)
            elevated.inspection_ids.unlink()
            elevated.report_id.unlink()
            elevated.scan_session_id.unlink()
        return super(AlfaCuoreBundle, self.sudo().with_context(cuore_import=True)).unlink()

    # ------------------------------------------------------------------------
    # Public service API (the wizard and any later REST route call these)
    # ------------------------------------------------------------------------
    def _check_can_import(self):
        if self.env.su:
            return
        user = self.env.user
        if not (
            user.has_group("alfa_core_cuore.group_cuore_mechanic")
            or user.has_group("alfa_core.group_advisor")
        ):
            raise AccessError(
                _("Only CUORE mechanics, service advisors and managers can import CUORE bundles.")
            )

    @api.model
    def inspect_bundle(self, data, order=None):
        """Validate and preview a bundle without writing anything.

        Returns a dict: ``errors``, ``warnings``, ``manifest``, ``parts``, ``summary``,
        ``vehicle``, ``existing`` (a bundle row with the same UUID), ``already``
        (True when that row is imported with identical content), ``prior`` / ``target``
        (the earlier bundle and record this one would supersede), ``sha256``.
        """
        self._check_can_import()
        Bundle = self.sudo()
        res = {
            "errors": [],
            "warnings": [],
            "manifest": {},
            "parts": {},
            "summary": {},
            "vehicle": self.env["alfa_fleet.vehicle"],
            "existing": Bundle.browse(),
            "already": False,
            "prior": Bundle.browse(),
            "target": None,
            "sha256": "",
        }
        if not data:
            res["errors"].append("No file was provided.")
            return res
        res["sha256"] = bundle_reader.sha256_hex(data)
        if len(data) > bundle_reader.MAX_ARCHIVE_BYTES:
            res["errors"].append(
                f"The file is larger than the {bundle_reader.MAX_ARCHIVE_BYTES // 2**20} MB cap."
            )
            return res
        errors = bundle_schema.validate_bundle(data)
        if errors:
            res["errors"] = errors
            res["manifest"] = bundle_reader.peek_manifest(data)
            res["existing"] = self._find_row(res["manifest"].get("bundle_uuid"))
            return res

        manifest, parts = bundle_reader.read_bundle(data)
        res["manifest"], res["parts"] = manifest, parts
        sem_errors, sem_warnings = bundle_reader.semantic_errors(manifest, parts)
        res["errors"] += sem_errors
        res["warnings"] += sem_warnings
        res["warnings"] += [f"CUORE: {w}" for w in manifest.get("warnings") or []]
        res["summary"] = bundle_reader.summarise(manifest, parts)

        existing = self._find_row(manifest["bundle_uuid"])
        res["existing"] = existing
        if existing and existing.state in ("imported", "superseded"):
            if existing.file_sha256 == res["sha256"]:
                res["already"] = True
            else:
                res["errors"].append(
                    "This bundle UUID was already imported with different content. "
                    "A correction is a new scan or job export, not an edited file."
                )
            return res

        vin = manifest["vehicle"]["vin"]
        vehicle = self.env["alfa_fleet.vehicle"].sudo().search([("vin", "=", vin)], limit=1)
        res["vehicle"] = vehicle
        if not vehicle:
            res["errors"].append(
                "No vehicle with this VIN exists in AlfaCore. The importer never creates "
                "vehicles or customers: create the vehicle first, then import again."
            )
        if order:
            order_vin = order.sudo().alfa_vehicle_id.vin
            if not order_vin:
                res["errors"].append(
                    f"Service order {order.display_name} has no vehicle; cannot confirm the VIN."
                )
            elif order_vin != vin:
                res["errors"].append(
                    f"VIN mismatch: the bundle is for {vin} but service order "
                    f"{order.display_name} is for {order_vin}. Nothing was imported."
                )
        res["warnings"] += self._time_warnings(manifest)
        if vehicle:
            self._check_supersession(res, manifest, vehicle)
        return res

    @api.model
    def import_bundle(self, data, filename="", order=None):
        """Import one bundle. Returns the bundle row (``state`` tells the outcome)."""
        return self._import(data, filename, order)["bundle"]

    @api.model
    def _import(self, data, filename="", order=None):
        """Import one bundle. Returns ``{outcome, bundle, errors, warnings}`` where outcome is
        ``imported``, ``already`` (nothing created), ``rejected`` or ``failed``."""
        res = self.inspect_bundle(data, order)
        out = {
            "outcome": "rejected",
            "bundle": res["existing"],
            "errors": res["errors"],
            "warnings": res["warnings"],
        }
        if res["already"]:
            out["outcome"] = "already"
            return out
        if res["errors"]:
            if res["existing"].state in ("imported", "superseded"):
                return out  # never touch an imported row
            row = self._record_rejection(res, data, filename, order)
            out["bundle"] = row
            return out

        manifest, parts = res["manifest"], res["parts"]
        row = self._upsert_row(res, data, filename, order, state="validated")
        try:
            with self.env.cr.savepoint():
                row._write_records(manifest, parts, order, res)
        except Exception as exc:
            _logger.exception("CUORE bundle %s failed to import", manifest.get("bundle_uuid"))
            row = self.sudo().browse(row.id)
            message = f"Import failed and was rolled back: {exc}"
            row.with_context(cuore_import=True).write(
                {
                    "state": "failed",
                    "validation_report": self._report_text([message], res["warnings"]),
                }
            )
            out.update(outcome="failed", bundle=row, errors=[message])
            return out
        out.update(outcome="imported", bundle=row)
        return out

    # ------------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------------
    @api.model
    def _find_row(self, bundle_uuid):
        if not isinstance(bundle_uuid, str) or not UUID_RE.match(bundle_uuid):
            return self.sudo().browse()
        return self.sudo().search([("bundle_uuid", "=", bundle_uuid)], limit=1)

    @api.model
    def _time_warnings(self, manifest):
        warnings = []
        created = bundle_reader.parse_aware_iso(manifest.get("created_at"))
        if created:
            age = fields.Datetime.now() - created
            max_days = int(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("alfa_core_cuore.max_bundle_age_days", DEFAULT_MAX_AGE_DAYS)
            )
            if age.total_seconds() < -300:
                warnings.append(
                    "The bundle is dated in the future; check the clock on the CUORE PC."
                )
            elif age.days > max_days:
                warnings.append(
                    f"The bundle is {age.days} days old (limit {max_days}); "
                    "the car may have changed since."
                )
        return warnings

    @api.model
    def _external_key(self, manifest):
        return f"{manifest['station_id']}:{manifest['source_id']}"

    @api.model
    def _check_supersession(self, res, manifest, vehicle):
        """A later bundle for the same scan or job updates the earlier one while that one is
        not finalized; a finalized one is never updated (integration spec 4.3)."""
        key = self._external_key(manifest)
        if manifest["kind"] == "scan":
            target = (
                self.env["alfa_core_scanner.scan_session"]
                .sudo()
                .search([("cuore_external_key", "=", key)], limit=1)
            )
        else:
            target = (
                self.env["alfa_core_diagnosis.report"]
                .sudo()
                .search([("cuore_job_key", "=", key)], limit=1)
            )
        if not target:
            return
        res["target"] = target
        prior = target.cuore_bundle_id
        res["prior"] = prior
        if target.vehicle_id != vehicle:
            res["errors"].append(
                "This scan or job was imported earlier for a different vehicle; refusing to move it."
            )
            return
        if prior.finalized:
            res["errors"].append(
                f"This {manifest['kind']} was already imported as final in {prior.name}. "
                "A finalized record is never updated; a correction is a new scan or job."
            )
            return
        prior_created = prior.created_at
        created = bundle_reader.parse_aware_iso(manifest.get("created_at"))
        if prior_created and created and created <= prior_created:
            res["errors"].append(
                f"{prior.name} (already imported) is newer than or as new as this bundle; "
                "an older export never replaces a newer one."
            )
        else:
            res["warnings"].append(
                f"This bundle supersedes {prior.name}: the earlier import will be updated."
            )

    @staticmethod
    def _report_text(errors, warnings):
        lines = [f"ERROR: {e}" for e in errors] + [f"WARNING: {w}" for w in warnings]
        return "\n".join(lines) if lines else "OK: schema, hashes and VIN checks passed."

    # ------------------------------------------------------------------------
    # Row bookkeeping
    # ------------------------------------------------------------------------
    @api.model
    def _safe_header(self, manifest):
        """Header fields from a manifest that may be invalid: only sane values are kept."""
        m = manifest if isinstance(manifest, dict) else {}
        vehicle = m.get("vehicle") if isinstance(m.get("vehicle"), dict) else {}
        station = m.get("station_id")
        vin = vehicle.get("vin")
        created = bundle_reader.parse_aware_iso(m.get("created_at"))
        return {
            "schema_version": str(m.get("schema") or "")[:32],
            "station_id": station if isinstance(station, str) and STATION_RE.match(station) else "",
            "kind": m.get("kind") if m.get("kind") in ("scan", "job") else False,
            "source_id": str(m.get("source_id") or "")[:128],
            "vin": vin if isinstance(vin, str) and VIN_RE.match(vin) else "",
            "cuore_version": str(m.get("cuore_version") or "")[:64],
            "created_at": created or False,
            "created_at_local": str(m.get("created_at") or "")[:64],
            "tz": str(m.get("tz") or "")[:64],
            "finalized": bool(m.get("finalized", True)),
        }

    @api.model
    def _upsert_row(self, res, data, filename, order, state):
        manifest = res["manifest"]
        elevated = self.sudo().with_context(cuore_import=True)
        vals = {
            **self._safe_header(manifest),
            "bundle_uuid": manifest["bundle_uuid"],
            "state": state,
            "file_sha256": res["sha256"],
            "filename": os.path.basename(str(filename or "").replace("\\", "/"))[:200],
            "validation_report": self._report_text(res["errors"], res["warnings"]),
            "vehicle_id": res["vehicle"].id or False,
            "sale_order_id": order.id if order else False,
        }
        row = elevated.search([("bundle_uuid", "=", manifest["bundle_uuid"])], limit=1)
        if row:
            row.attachment_id.unlink()
            row.write(vals)
        else:
            row = elevated.create(vals)
        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": vals["filename"] or f"{manifest['bundle_uuid']}.cuore.zip",
                    "datas": base64.b64encode(data),
                    "res_model": self._name,
                    "res_id": row.id,
                    "mimetype": "application/zip",
                }
            )
        )
        row.write({"attachment_id": attachment.id})
        return row

    @api.model
    def _record_rejection(self, res, data, filename, order):
        """Keep a failed row (with the file) when the manifest names a usable UUID."""
        manifest = res["manifest"]
        uuid_ = manifest.get("bundle_uuid") if isinstance(manifest, dict) else None
        if not (isinstance(uuid_, str) and UUID_RE.match(uuid_)):
            return self.sudo().browse()
        res = dict(res, manifest={**manifest, "bundle_uuid": uuid_})
        return self._upsert_row(res, data, filename, order, state="failed")

    # ------------------------------------------------------------------------
    # Writing the records (always inside the caller's savepoint, importer context)
    # ------------------------------------------------------------------------
    def _write_records(self, manifest, parts, order, res):
        self.ensure_one()
        user_id = self.env.uid
        rec = self.sudo().with_context(cuore_import=True)
        vehicle = res["vehicle"].sudo()
        prior = res["prior"]
        target = res["target"].with_context(cuore_import=True) if res["target"] else None
        vals = {
            "state": "imported",
            "imported_at": fields.Datetime.now(),
            "imported_by_id": user_id,
            "validation_report": self._report_text([], res["warnings"]),
            "code_findings_json": json_text(parts.get("code_findings.json")),
            "tsb_xref_json": json_text(parts.get("tsb_xref.json")),
        }
        summary = res["summary"]
        if manifest["kind"] == "scan":
            session = rec._import_scan(manifest, parts, vehicle, target)
            vals.update(scan_session_id=session.id, dtc_count=summary["dtc_rows"])
            report = rec.env["alfa_core_diagnosis.report"]
            inspections = rec.env["alfa_core_inspection.inspection"]
        else:
            report, session, inspections = rec._import_job(manifest, parts, vehicle, order, target)
            vals.update(
                scan_session_id=session.id,
                report_id=report.id,
                inspection_ids=[(6, 0, inspections.ids)],
                hypothesis_count=summary["hypotheses"],
                step_count=summary["steps"],
            )
        if prior:
            prior.sudo().with_context(cuore_import=True).write(
                {
                    "state": "superseded",
                    "scan_session_id": False,
                    "report_id": False,
                    "inspection_ids": [(5, 0, 0)],
                }
            )
        rec.write(vals)
        rec.message_post(
            body=_(
                "Imported by %(user)s: %(kind)s bundle from station %(station)s, "
                "%(dtc)s DTC rows, %(hyp)s hypotheses, %(steps)s steps.",
                user=self.env.user.name,
                kind=manifest["kind"],
                station=manifest["station_id"],
                dtc=summary["dtc_rows"],
                hyp=summary["hypotheses"],
                steps=summary["steps"],
            )
        )

    def _get_device(self, manifest):
        Device = self.env["alfa_core_scanner.device"]
        serial = f"CUORE-{manifest['station_id']}"
        device = Device.search([("serial_number", "=", serial)], limit=1)
        if not device:
            device = Device.create(
                {
                    "serial_number": serial,
                    "model_name": "cuore_stn",
                    "state": "active",
                    "cuore_station_id": manifest["station_id"],
                    "cuore_transport": "serial_usb",
                }
            )
        return device

    def _session_vals(self, manifest, vehicle, device, role, started, ended):
        return {
            "vehicle_id": vehicle.id,
            "device_id": device.id,
            "started_at": started or fields.Datetime.now(),
            "ended_at": ended or False,
            "inference_zde": True,
            "cuore_bundle_id": self.id,
            "cuore_source": "CUORE wired adapter",
            "cuore_session_role": role,
            "cuore_finalized": bool(manifest.get("finalized", True)),
        }

    def _import_scan(self, manifest, parts, vehicle, target):
        Session = self.env["alfa_core_scanner.scan_session"]
        Dtc = self.env["alfa_core_scanner.scan_dtc"]
        scan = parts["scan.json"]
        created = bundle_reader.parse_aware_iso(manifest["created_at"])
        window = scan.get("window") or {}
        started = bundle_reader.parse_aware_iso(window.get("start_iso")) or created
        ended = bundle_reader.parse_aware_iso(window.get("end_iso"))
        rows, counts = bundle_reader.dtc_rows(parts)
        coverage = scan.get("coverage") or []
        answered = []
        for c in coverage:
            module = c.get("module") if isinstance(c, dict) else None
            if module and c.get("category") == "answered" and module not in answered:
                answered.append(str(module))
        sent_counts = scan.get("counts") or {}
        ff = parts.get("freeze_frames.json") or {}
        vals = self._session_vals(
            manifest, vehicle, self._get_device(manifest), "scan", started, ended
        )
        vals.update(
            {
                "state": "uploaded",
                "modules_scanned": ",".join(answered),
                "cuore_external_key": self._external_key(manifest),
                "cuore_scan_status": scan.get("status"),
                "cuore_from_car": bool(scan.get("from_car")),
                "cuore_stream": ", ".join(str(s) for s in scan.get("streams") or []),
                "cuore_cable": str(scan.get("cable") or ""),
                "cuore_buses_attempted": ", ".join(
                    str(b) for b in scan.get("buses_attempted") or []
                ),
                "cuore_count_active": int(sent_counts.get("active", counts["active"]) or 0),
                "cuore_count_history": int(sent_counts.get("history", counts["history"]) or 0),
                "cuore_count_not_run": int(sent_counts.get("not_run", counts["not_run"]) or 0),
                "cuore_freeze_frame_json": json_text(
                    {"mode02": ff.get("mode02") or [], "dtc_detail": ff.get("dtc_detail") or []}
                ),
                "cuore_mode06_json": json_text((parts.get("mode06.json") or {}).get("records")),
                "cuore_coverage_json": json_text(coverage),
                "cuore_readiness_json": json_text(
                    (parts.get("readiness.json") or {}).get("records")
                ),
                "cuore_requirements_json": json_text(parts.get("scan_requirements.json")),
                "cuore_scan_meta_json": json_text(
                    {
                        "guided": scan.get("guided"),
                        "steps": scan.get("steps"),
                        "counts": scan.get("counts"),
                        "window": window,
                        "evap_bundle": parts.get("evap_bundle.json"),
                    }
                ),
            }
        )
        if target:
            target.dtc_ids.unlink()
            target.write(vals)
            session = target
        else:
            session = Session.create(vals)
        Dtc.create(
            [
                {
                    "scan_session_id": session.id,
                    "dtc_code": r["dtc_code"],
                    "dtc_status": r["dtc_status"],
                    "module_source": r["module_source"],
                    "raw_payload": r["raw_payload"],
                    "cuore_imported": True,
                    "cuore_from_car": r["from_car"],
                    "status_byte": r["status_byte"],
                    "status_flags_json": json_text(r["flags"]),
                    "failure_type_byte": r["failure_type_byte"],
                    "bus": r["bus"],
                    "source_service": r["source_service"] or False,
                    "sequence": 10 * (i + 1),
                }
                for i, r in enumerate(rows)
            ]
        )
        return session

    def _import_job(self, manifest, parts, vehicle, order, target):
        Session = self.env["alfa_core_scanner.scan_session"]
        Report = self.env["alfa_core_diagnosis.report"]
        job = parts["job.json"]["job"]
        key = self._external_key(manifest)
        created = bundle_reader.parse_aware_iso(manifest["created_at"])
        hyps = bundle_reader.hypothesis_rows(parts)

        # A report needs a scan session; a job carries none, so an empty anchor holds the
        # link. It has no DTCs and is marked as not from the car.
        anchor_vals = self._session_vals(
            manifest, vehicle, self._get_device(manifest), "job_anchor", created, None
        )
        anchor_vals.update(
            {
                "state": "complete",
                "cuore_external_key": f"job:{key}",
                "cuore_from_car": False,
            }
        )
        if target:
            anchor = target.scan_session_id
            anchor.write(anchor_vals)
        else:
            anchor = Session.create(anchor_vals)

        unresolved_safety = any(
            h["safety"]
            and not h["deleted"]
            and not h["attested_resolved"]
            and h["status"] != "refuted"
            for h in hyps
        )
        proof = parts.get("proof_of_fix.json") or {}
        criteria_lines = [
            f"[{str(c.get('evidence_class') or 'inference').upper()}] "
            f"{c.get('code') or '?'}"
            f"{' (' + str(c['module']) + ')' if c.get('module') else ''}: {c.get('proof') or ''}"
            for c in proof.get("criteria") or []
            if isinstance(c, dict)
        ]
        vals = {
            "scan_session_id": anchor.id,
            "cuore_bundle_id": self.id,
            "inference_zde": True,
            "technical_summary": bundle_reader.template_technical_summary(manifest, parts),
            "cuore_job_key": key,
            "cuore_job_id": str(job.get("id") or ""),
            "cuore_station_id": manifest["station_id"],
            "cuore_job_status": str(job.get("status") or ""),
            "cuore_job_outcome": str(job.get("outcome") or ""),
            "cuore_complaint": str(job.get("complaint") or ""),
            "cuore_technician": str(job.get("technician") or ""),
            "cuore_proof_present": bool(proof.get("present")),
            "cuore_proof_criteria": "\n".join(criteria_lines) or False,
            "cuore_proof_json": json_text(
                {
                    k: proof.get(k)
                    for k in ("present", "criteria", "verification", "outcome", "clear_evidence")
                }
            ),
        }
        if unresolved_safety:
            vals["severity"] = "safety_critical"
        # The importer only ever sets draft / pending_review; review is a person's decision.
        wanted_state = "pending_review" if job.get("status") == "closed" else "draft"
        if target:
            report = target
            if report.state in ("draft", "ai_generated", "pending_review"):
                vals["state"] = wanted_state
            else:
                report.message_post(
                    body=_(
                        "The CUORE ledger changed after this report was reviewed. "
                        "Statuses and evidence were updated; please review again."
                    )
                )
            report.hypothesis_ids.unlink()
            report.write(vals)
        else:
            vals["state"] = wanted_state
            report = Report.create(vals)

        self.env["alfa.cuore.hypothesis"].create(
            [
                {
                    "report_id": report.id,
                    "bundle_id": self.id,
                    "hyp_id": h["hyp_id"],
                    "external_key": f"{key}:{h['hyp_id']}",
                    "text": h["text"] or h["hyp_id"],
                    "system": h["system"],
                    "status": h["status"],
                    "likelihood": h["likelihood"],
                    "next_test": h["next_test"],
                    "codes": h["codes"],
                    "safety": h["safety"],
                    "attested_resolved": h["attested_resolved"],
                    "deleted": h["deleted"],
                    "evidence_class": h["evidence_class"],
                    "evidence_class_basis": h["evidence_class_basis"],
                    "audit_json": json_text(h["audit"]),
                    "evidence_ids": [
                        (
                            0,
                            0,
                            {
                                "side": e["side"],
                                "kind": e["kind"],
                                "ref_id": e["ref_id"],
                                "label": e["label"],
                                "result": e["result"],
                                "evidence_class": e["evidence_class"] or "inference",
                            },
                        )
                        for e in h["evidence"]
                    ],
                }
                for h in hyps
            ]
        )
        inspections = self._import_plans(manifest, parts, vehicle, order, key)
        return report, anchor, inspections

    def _import_plans(self, manifest, parts, vehicle, order, job_key):
        Inspection = self.env["alfa_core_inspection.inspection"]
        template = self.env.ref("alfa_core_cuore.template_cuore_plan")
        plans = bundle_reader.plan_rows(parts)
        wanted_keys = {f"{job_key}:{p['hypothesis_id']}" for p in plans}
        # Plans that no longer exist in the newer snapshot are removed (CUORE is the authority).
        stale = Inspection.search(
            [
                ("cuore_hyp_key", "=like", f"{job_key}:%"),
                ("cuore_hyp_key", "not in", list(wanted_keys)),
            ]
        )
        stale.unlink()
        result = Inspection
        for plan in plans:
            hyp_key = f"{job_key}:{plan['hypothesis_id']}"
            lines = [self._finding_vals(s) for s in plan["steps"]]
            inspection = Inspection.search([("cuore_hyp_key", "=", hyp_key)], limit=1)
            if inspection:
                by_key = {f.step_key: f for f in inspection.finding_ids}
                new_keys = {s["step_key"] for s in plan["steps"]}
                inspection.finding_ids.filtered(
                    lambda f, keys=new_keys: f.step_key not in keys
                ).unlink()
                inspection.write({"cuore_bundle_id": self.id})
                for line in lines:
                    existing = by_key.get(line["step_key"])
                    if existing:
                        existing.write(line)
                    else:
                        inspection.write({"finding_ids": [(0, 0, line)]})
            else:
                inspection = Inspection.create(
                    {
                        "template_id": template.id,
                        "vehicle_id": vehicle.id,
                        "sale_order_id": order.id if order else False,
                        "technician_id": order.alfa_technician_id.id if order else False,
                        "bay_id": order.alfa_bay_id.id if order else False,
                        "inference_zde": True,
                        "cuore_bundle_id": self.id,
                        "cuore_hyp_key": hyp_key,
                        # Giving findings up front stops the template from adding its own.
                        "finding_ids": [(0, 0, line) for line in lines],
                    }
                )
            result |= inspection
        return result

    @staticmethod
    def _finding_vals(step):
        return {
            "name": step["name"] or _("(untitled step)"),
            "sequence": 10 * (step["step_order"] + 1),
            "category": "other",
            "measurement_type": "text" if step["step_kind"] in STEP_TEXT_KINDS else "pass_fail",
            "note": step["note"],
            # A done process step is "pass" meaning completed. It is not a test verdict.
            "state": "pass" if step["step_done"] else "not_checked",
            "remediation_recommended": False,
            "step_key": step["step_key"],
            "step_order": step["step_order"],
            "step_kind": step["step_kind"],
            "step_source": step["step_source"],
            "step_tools": step["step_tools"],
            "step_bulletins": step["step_bulletins"],
            "step_done": step["step_done"],
            "step_done_ref": step["step_done_ref"],
            "evidence_class": step["evidence_class"] or "inference",
        }

    # ------------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------------
    def action_open_scan_session(self):
        self.ensure_one()
        return self._open(self.scan_session_id)

    def action_open_report(self):
        self.ensure_one()
        return self._open(self.report_id)

    @api.model
    def _open(self, record):
        return {
            "type": "ir.actions.act_window",
            "res_model": record._name,
            "res_id": record.id,
            "view_mode": "form",
        }


__all__ = ["EVIDENCE_CLASSES", "AlfaCuoreBundle", "json_text"]
