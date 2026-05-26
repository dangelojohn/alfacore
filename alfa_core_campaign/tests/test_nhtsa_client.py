# SPDX-License-Identifier: LGPL-3.0-only
"""NHTSA HTTP client tests — mocked requests, no real network calls."""

from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase, tagged

# A representative NHTSA Recalls API response payload, with one safety-critical
# (parkIt) recall and one normal recall, mirroring the documented schema.
NHTSA_SAMPLE_RESPONSE = {
    "Count": 2,
    "Message": "Results returned successfully",
    "results": [
        {
            "NHTSACampaignNumber": "TEST-24V100000",
            "Manufacturer": "FCA US LLC",
            "ReportReceivedDate": "15/03/2024",
            "Component": "FUEL SYSTEM, GASOLINE: DELIVERY: FUEL PUMP",
            "Summary": "Test recall: fuel pump driver module may fail.",
            "Consequence": "Engine may stall, increasing crash risk.",
            "Remedy": "Dealer will replace the fuel pump driver module.",
            "parkIt": False,
            "parkOutSide": False,
            "overTheAirUpdate": False,
        },
        {
            "NHTSACampaignNumber": "TEST-24V200000",
            "Manufacturer": "FCA US LLC",
            "ReportReceivedDate": "08/06/2024",
            "Component": "ELECTRICAL SYSTEM: BATTERY",
            "Summary": "Test recall: battery thermal event possible.",
            "Consequence": "May cause fire while parked.",
            "Remedy": "Pending. Park outside until remedy is available.",
            "parkIt": True,
            "parkOutSide": True,
            "overTheAirUpdate": False,
        },
    ],
}


@tagged("post_install", "-at_install", "alfacore_sprint12_nhtsa")
class TestNhtsaClient(TransactionCase):
    def _mock_requests_get(self, payload, status_code=200):
        """Build a MagicMock that imitates a successful requests.get response."""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = payload
        mock_response.raise_for_status = MagicMock()
        if status_code >= 400:
            import requests

            err = requests.exceptions.HTTPError()
            err.response = mock_response
            mock_response.raise_for_status.side_effect = err
        return mock_response

    # ------------------------------------------------------------------------
    # Fetch path
    # ------------------------------------------------------------------------
    def test_fetch_returns_results_list(self):
        client = self.env["alfa_core_campaign.nhtsa_client"]
        with patch("requests.get") as mock_get:
            mock_get.return_value = self._mock_requests_get(NHTSA_SAMPLE_RESPONSE)
            results = client._fetch_nhtsa_recalls("Alfa Romeo", "Stelvio", 2019)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["NHTSACampaignNumber"], "TEST-24V100000")

    def test_fetch_empty_response(self):
        client = self.env["alfa_core_campaign.nhtsa_client"]
        with patch("requests.get") as mock_get:
            mock_get.return_value = self._mock_requests_get({"Count": 0, "results": []})
            results = client._fetch_nhtsa_recalls("Alfa Romeo", "Stelvio", 1990)
        self.assertEqual(results, [])

    def test_fetch_4xx_returns_empty_no_retry(self):
        """4xx responses are not retried — they're stable client-side errors."""
        client = self.env["alfa_core_campaign.nhtsa_client"]
        with patch("requests.get") as mock_get:
            mock_get.return_value = self._mock_requests_get({}, status_code=400)
            results = client._fetch_nhtsa_recalls("Bad", "Make", 2024)
        self.assertEqual(results, [])
        # Only called once — no retry on 4xx
        self.assertEqual(mock_get.call_count, 1)

    def test_fetch_handles_non_list_results(self):
        """Defensive: NHTSA returns something weird, we return empty not crash."""
        client = self.env["alfa_core_campaign.nhtsa_client"]
        with patch("requests.get") as mock_get:
            mock_get.return_value = self._mock_requests_get({"results": "not a list"})
            results = client._fetch_nhtsa_recalls("Alfa Romeo", "Stelvio", 2019)
        self.assertEqual(results, [])

    # ------------------------------------------------------------------------
    # Upsert path
    # ------------------------------------------------------------------------
    def test_upsert_creates_campaign_with_severity_mapping(self):
        client = self.env["alfa_core_campaign.nhtsa_client"]
        record = NHTSA_SAMPLE_RESPONSE["results"][1]  # the parkIt=True one
        campaign, is_new = client.upsert_campaign_from_nhtsa_record(record)
        self.assertTrue(is_new)
        self.assertEqual(campaign.source_id, "TEST-24V200000")
        # parkIt+parkOutSide should map to safety_critical
        self.assertEqual(campaign.severity, "safety_critical")
        self.assertIn("PARK IT", campaign.remedy_summary)
        self.assertIn("PARK OUTSIDE", campaign.remedy_summary)

    def test_upsert_default_severity_for_normal_recall(self):
        client = self.env["alfa_core_campaign.nhtsa_client"]
        record = NHTSA_SAMPLE_RESPONSE["results"][0]  # no park flags
        campaign, _is_new = client.upsert_campaign_from_nhtsa_record(record)
        self.assertEqual(campaign.severity, "high")

    def test_upsert_is_idempotent(self):
        """Calling upsert twice with the same record updates, doesn't duplicate."""
        client = self.env["alfa_core_campaign.nhtsa_client"]
        record = NHTSA_SAMPLE_RESPONSE["results"][0]
        first, was_new_first = client.upsert_campaign_from_nhtsa_record(record)
        second, was_new_second = client.upsert_campaign_from_nhtsa_record(record)
        self.assertTrue(was_new_first)
        self.assertFalse(was_new_second)
        self.assertEqual(first.id, second.id)

    def test_upsert_missing_campaign_number_returns_empty(self):
        client = self.env["alfa_core_campaign.nhtsa_client"]
        bad_record = {"Manufacturer": "Test", "Summary": "no campaign number"}
        campaign, is_new = client.upsert_campaign_from_nhtsa_record(bad_record)
        self.assertFalse(campaign)
        self.assertFalse(is_new)

    def test_upsert_parses_date_correctly(self):
        client = self.env["alfa_core_campaign.nhtsa_client"]
        record = NHTSA_SAMPLE_RESPONSE["results"][0]  # date "15/03/2024"
        campaign, _ = client.upsert_campaign_from_nhtsa_record(record)
        self.assertEqual(str(campaign.issued_date), "2024-03-15")

    def test_upsert_handles_malformed_date_gracefully(self):
        client = self.env["alfa_core_campaign.nhtsa_client"]
        record = {**NHTSA_SAMPLE_RESPONSE["results"][0], "ReportReceivedDate": "not a date"}
        record["NHTSACampaignNumber"] = "TEST-DATE-001"
        campaign, _ = client.upsert_campaign_from_nhtsa_record(record)
        # Campaign still created; date just not set
        self.assertTrue(campaign)
        self.assertFalse(campaign.issued_date)

    # ------------------------------------------------------------------------
    # Full poll orchestration
    # ------------------------------------------------------------------------
    def test_poll_iterates_fleet_groups(self):
        """poll_nhtsa should read_group the fleet and call _fetch once per tuple."""
        # Create two Alfa Romeo Stelvio vehicles (same year) and one Giulia.
        # That's 2 unique (make, model, year) tuples for read_group → 2 HTTP calls.
        Vehicle = self.env["alfa_fleet.vehicle"]
        Vehicle.create(
            {
                "vin": "ZASFAKBN3J7CPOL01",
                "make": "Alfa Romeo",
                "model": "Stelvio",
                "year": 2018,
            }
        )
        Vehicle.create(
            {
                "vin": "ZASFAKBN3K7CPOL02",
                "make": "Alfa Romeo",
                "model": "Stelvio",
                "year": 2018,
            }
        )
        Vehicle.create(
            {
                "vin": "ZARFAEBN8L7CPOL03",
                "make": "Alfa Romeo",
                "model": "Giulia",
                "year": 2020,
            }
        )
        client = self.env["alfa_core_campaign.nhtsa_client"]
        with patch.object(client.__class__, "_fetch_nhtsa_recalls") as mock_fetch:
            mock_fetch.return_value = []  # no recalls returned
            # also patch time.sleep so the test doesn't actually wait
            with patch("time.sleep"):
                summary = client.poll_nhtsa()
        # Should have called _fetch_nhtsa_recalls for 2 unique tuples (NB: pre-existing
        # demo data may also contribute — assert at least 2)
        self.assertGreaterEqual(mock_fetch.call_count, 2)
        self.assertGreaterEqual(summary["tuples_queried"], 2)
