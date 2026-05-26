# SPDX-License-Identifier: LGPL-3.0-only
"""Allocation state machine + date math tests."""

from datetime import date, timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint9")
class TestAllocationWorkflow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create({"name": "Loaner Customer"})
        cls.loaner = cls.env["alfa_core_loaner.vehicle"].create(
            {
                "name": "Test Loaner",
                "license_plate": "TEST 001",
                "year": 2023,
                "model_name": "Stelvio Ti",
                "current_mileage_km": 10000,
            }
        )

    def _allocation_defaults(self):
        today = date.today()
        return {
            "loaner_vehicle_id": self.loaner.id,
            "partner_id": self.customer.id,
            "pickup_date": today,
            "scheduled_return_date": today + timedelta(days=3),
        }

    def test_sequence_assigned(self):
        a = self.env["alfa_core_loaner.allocation"].create(self._allocation_defaults())
        self.assertNotEqual(a.name, "New")
        self.assertTrue(a.name.startswith("AC-LOAN-"))

    def test_return_before_pickup_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["alfa_core_loaner.allocation"].create(
                {
                    **self._allocation_defaults(),
                    "scheduled_return_date": date.today() - timedelta(days=1),
                }
            )

    def test_schedule_sets_loaner_to_allocated(self):
        a = self.env["alfa_core_loaner.allocation"].create(self._allocation_defaults())
        a.action_schedule()
        self.assertEqual(a.state, "scheduled")
        self.assertEqual(self.loaner.state, "allocated")

    def test_cannot_schedule_unavailable_loaner(self):
        self.loaner.state = "maintenance"
        a = self.env["alfa_core_loaner.allocation"].create(self._allocation_defaults())
        with self.assertRaises(UserError):
            a.action_schedule()

    def test_activation_requires_signature(self):
        a = self.env["alfa_core_loaner.allocation"].create(self._allocation_defaults())
        a.action_schedule()
        with self.assertRaises(UserError):
            a.action_activate()

    def test_send_for_signature_flips_status(self):
        a = self.env["alfa_core_loaner.allocation"].create(self._allocation_defaults())
        a.action_send_for_signature()
        self.assertEqual(a.sign_status, "sent")

    def test_days_overage_compute(self):
        today = date.today()
        a = self.env["alfa_core_loaner.allocation"].create(
            {
                **self._allocation_defaults(),
                "actual_return_date": today + timedelta(days=5),  # 2 days late
            }
        )
        self.assertEqual(a.days_overage, 2)

    def test_return_releases_loaner(self):
        a = self.env["alfa_core_loaner.allocation"].create(self._allocation_defaults())
        a.action_schedule()
        # Simulate signature flow and pickup
        a.sign_status = "signed"
        pickup_report = self.env["alfa_core_loaner.condition_report"].create(
            {
                "report_type": "pickup",
                "mileage_km": 10000,
            }
        )
        a.pickup_report_id = pickup_report.id
        a.action_activate()
        self.assertEqual(a.state, "active")

        return_report = self.env["alfa_core_loaner.condition_report"].create(
            {
                "report_type": "return",
                "mileage_km": 10500,
            }
        )
        a.return_report_id = return_report.id
        a.return_mileage_km = 10500
        a.actual_return_date = a.pickup_date + timedelta(days=2)
        a.action_return()
        self.assertEqual(a.state, "returned")
        self.assertEqual(self.loaner.state, "available")
        self.assertEqual(a.miles_driven, 500)
