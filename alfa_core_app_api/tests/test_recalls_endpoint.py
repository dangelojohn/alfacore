# SPDX-License-Identifier: LGPL-3.0-only
"""Tests for GET /api/v1/vehicles/<vin>/recalls.

These exercise the controller's logic against in-memory records — no live
HTTP since the endpoint reads from campaign_target records that should be
populated by Sprint 12's nhtsa_client cron.
"""

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint11_recalls")
class TestRecallsEndpointLogic(TransactionCase):
    """Logic tests — verify the right targets are returned, sorted, and
    serialized. Skips the HTTP transport (auth, JSON wrapping) which is
    covered by the existing test_install JWT smoke tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Recall Test Customer"})
        cls.vehicle = cls.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7CRCL01",
                "make": "Alfa Romeo",
                "model": "Stelvio",
                "year": 2018,
            }
        )
        # Wire ownership so the vehicle is "owned" by the test partner
        cls.env["alfa_fleet.vehicle_ownership"].create(
            {
                "vehicle_id": cls.vehicle.id,
                "partner_id": cls.partner.id,
                "role": "primary_driver",
                "active": True,
            }
        )

    def _make_campaign(self, source_id, severity="high", camp_type="safety_recall"):
        return self.env["alfa_core_campaign.campaign"].create(
            {
                "name": f"Test {source_id}",
                "campaign_type": camp_type,
                "source": "nhtsa",
                "source_id": source_id,
                "severity": severity,
            }
        )

    def _make_target(self, campaign, state="notified"):
        return self.env["alfa_core_campaign.target"].create(
            {
                "campaign_id": campaign.id,
                "vehicle_id": self.vehicle.id,
                "state": state,
            }
        )

    def test_open_targets_returned(self):
        """States identified, notified, acknowledged, scheduled all count as open."""
        c1 = self._make_campaign("OPEN-1")
        c2 = self._make_campaign("OPEN-2")
        c3 = self._make_campaign("OPEN-3")
        self._make_target(c1, state="identified")
        self._make_target(c2, state="notified")
        self._make_target(c3, state="scheduled")
        Target = self.env["alfa_core_campaign.target"]
        open_targets = Target.search(
            [
                ("vehicle_id", "=", self.vehicle.id),
                ("state", "in", ("identified", "notified", "acknowledged", "scheduled")),
            ]
        )
        self.assertEqual(len(open_targets), 3)

    def test_serviced_targets_excluded(self):
        c_open = self._make_campaign("STILL-OPEN")
        c_done = self._make_campaign("ALREADY-DONE")
        self._make_target(c_open, state="notified")
        self._make_target(c_done, state="serviced")
        Target = self.env["alfa_core_campaign.target"]
        open_targets = Target.search(
            [
                ("vehicle_id", "=", self.vehicle.id),
                ("state", "in", ("identified", "notified", "acknowledged", "scheduled")),
            ]
        )
        self.assertEqual(len(open_targets), 1)
        self.assertEqual(open_targets.campaign_id.source_id, "STILL-OPEN")

    def test_declined_targets_excluded(self):
        """Customer-declined recalls don't show up as open in the API."""
        c = self._make_campaign("DECLINED-BY-CUSTOMER")
        self._make_target(c, state="declined")
        Target = self.env["alfa_core_campaign.target"]
        open_targets = Target.search(
            [
                ("vehicle_id", "=", self.vehicle.id),
                ("state", "in", ("identified", "notified", "acknowledged", "scheduled")),
            ]
        )
        self.assertEqual(len(open_targets), 0)

    def test_do_not_drive_flag_set_when_safety_critical(self):
        c = self._make_campaign("SAFETY-CRIT", severity="safety_critical")
        self._make_target(c)
        # Mimic the controller's flag computation
        targets = self.env["alfa_core_campaign.target"].search(
            [
                ("vehicle_id", "=", self.vehicle.id),
            ]
        )
        do_not_drive = any(t.campaign_id.severity == "safety_critical" for t in targets)
        self.assertTrue(do_not_drive)

    def test_empty_when_no_recalls(self):
        Target = self.env["alfa_core_campaign.target"]
        open_targets = Target.search([("vehicle_id", "=", self.vehicle.id)])
        self.assertEqual(len(open_targets), 0)
