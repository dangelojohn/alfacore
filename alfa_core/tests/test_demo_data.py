# SPDX-License-Identifier: LGPL-3.0-only
"""Verify demo data loaded correctly."""

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint1")
class TestDemoData(TransactionCase):
    def test_three_plans_loaded(self):
        plans = self.env["alfa_core.subscription.plan"].search([])
        plan_codes = plans.mapped("code")
        for expected in ("basic", "premium", "pro"):
            self.assertIn(expected, plan_codes, f"Demo plan '{expected}' should be loaded")

    def test_plans_have_benefits(self):
        basic = self.env.ref("alfa_core.plan_basic")
        premium = self.env.ref("alfa_core.plan_premium")
        pro = self.env.ref("alfa_core.plan_pro")
        self.assertGreaterEqual(len(basic.features), 3)
        self.assertGreaterEqual(len(premium.features), 3)
        self.assertGreaterEqual(len(pro.features), 3)

    def test_zde_defaults(self):
        for code in ("basic", "premium", "pro"):
            plan = self.env["alfa_core.subscription.plan"].search([("code", "=", code)])
            self.assertTrue(
                plan.inference_zde_default,
                f"Plan {code} should default to ZDE inference per Service Plan §8.2",
            )
