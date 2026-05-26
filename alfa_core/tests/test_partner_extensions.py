# SPDX-License-Identifier: LGPL-3.0-only
"""Partner extension tests — tier compute, signup auto-stamp, PIPEDA."""

from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint1")
class TestPartnerExtensions(TransactionCase):
    def test_signup_auto_stamps_on_create(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Auto Signup",
                "alfa_core_customer": True,
            }
        )
        self.assertTrue(partner.alfa_core_signup_date)

    def test_signup_auto_stamps_on_write(self):
        partner = self.env["res.partner"].create({"name": "Later Signup"})
        self.assertFalse(partner.alfa_core_signup_date)
        partner.alfa_core_customer = True
        self.assertTrue(partner.alfa_core_signup_date)

    def test_tier_bronze_for_new_customer(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Bronze",
                "alfa_core_customer": True,
            }
        )
        partner._compute_alfa_core_customer_tier()
        self.assertEqual(partner.alfa_core_customer_tier, "bronze")

    def test_tier_silver_after_one_year(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Silver",
                "alfa_core_customer": True,
            }
        )
        partner.alfa_core_signup_date = fields.Datetime.now() - timedelta(days=400)
        partner._compute_alfa_core_customer_tier()
        self.assertEqual(partner.alfa_core_customer_tier, "silver")

    def test_tier_gold_after_three_years(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Gold",
                "alfa_core_customer": True,
            }
        )
        partner.alfa_core_signup_date = fields.Datetime.now() - timedelta(days=1200)
        partner._compute_alfa_core_customer_tier()
        self.assertEqual(partner.alfa_core_customer_tier, "gold")

    def test_default_preferred_channel_is_email(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Channel Default",
                "alfa_core_customer": True,
            }
        )
        self.assertEqual(partner.alfa_core_preferred_channel, "email")

    def test_active_subscription_compute(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Active Sub",
                "alfa_core_customer": True,
            }
        )
        plan = self.env["alfa_core.subscription.plan"].create(
            {
                "name": "Test",
                "code": "test_active",
            }
        )
        sub = self.env["alfa_core.subscription"].create(
            {
                "partner_id": partner.id,
                "plan_id": plan.id,
            }
        )
        sub.action_activate()
        partner._compute_active_subscription()
        self.assertEqual(partner.alfa_core_active_subscription_id, sub)
