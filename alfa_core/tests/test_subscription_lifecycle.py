# SPDX-License-Identifier: LGPL-3.0-only
"""Subscription state machine tests."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint1")
class TestSubscriptionLifecycle(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Customer",
                "alfa_core_customer": True,
            }
        )
        cls.plan = cls.env["alfa_core.subscription.plan"].create(
            {
                "name": "Test Plan",
                "code": "test_plan",
                "monthly_price": 19.99,
                "annual_price": 199.99,
            }
        )

    def test_create_assigns_sequence(self):
        sub = self.env["alfa_core.subscription"].create(
            {
                "partner_id": self.partner.id,
                "plan_id": self.plan.id,
            }
        )
        self.assertNotEqual(sub.name, "New")
        self.assertTrue(sub.name.startswith("AC-SUB-"))

    def test_default_state_is_trial(self):
        sub = self.env["alfa_core.subscription"].create(
            {
                "partner_id": self.partner.id,
                "plan_id": self.plan.id,
            }
        )
        self.assertEqual(sub.state, "trial")

    def test_activate_from_trial(self):
        sub = self.env["alfa_core.subscription"].create(
            {
                "partner_id": self.partner.id,
                "plan_id": self.plan.id,
            }
        )
        sub.action_activate()
        self.assertEqual(sub.state, "active")
        # Chatter should have logged the transition
        self.assertTrue(any("activated" in m.body.lower() for m in sub.message_ids))

    def test_cannot_activate_from_active(self):
        sub = self.env["alfa_core.subscription"].create(
            {
                "partner_id": self.partner.id,
                "plan_id": self.plan.id,
            }
        )
        sub.action_activate()
        with self.assertRaises(UserError):
            sub.action_activate()

    def test_past_due_then_recover(self):
        sub = self.env["alfa_core.subscription"].create(
            {
                "partner_id": self.partner.id,
                "plan_id": self.plan.id,
            }
        )
        sub.action_activate()
        sub.action_mark_past_due()
        self.assertEqual(sub.state, "past_due")
        sub.action_activate()
        self.assertEqual(sub.state, "active")

    def test_cancel_sets_end_date(self):
        sub = self.env["alfa_core.subscription"].create(
            {
                "partner_id": self.partner.id,
                "plan_id": self.plan.id,
            }
        )
        sub.action_cancel()
        self.assertEqual(sub.state, "cancelled")
        self.assertTrue(sub.end_date)

    def test_end_before_start_raises(self):
        from datetime import date, timedelta

        with self.assertRaises(ValidationError):
            self.env["alfa_core.subscription"].create(
                {
                    "partner_id": self.partner.id,
                    "plan_id": self.plan.id,
                    "start_date": date.today(),
                    "end_date": date.today() - timedelta(days=1),
                }
            )

    def test_zde_inherits_from_plan(self):
        plan_no_zde = self.env["alfa_core.subscription.plan"].create(
            {
                "name": "Cloud Plan",
                "code": "cloud_plan",
                "inference_zde_default": False,
            }
        )
        sub = self.env["alfa_core.subscription"].create(
            {
                "partner_id": self.partner.id,
                "plan_id": plan_no_zde.id,
            }
        )
        self.assertFalse(sub.inference_zde)
