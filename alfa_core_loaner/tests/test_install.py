# SPDX-License-Identifier: LGPL-3.0-only
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_installed(self):
        m = self.env["ir.module.module"].search([("name", "=", "alfa_core_loaner")])
        self.assertEqual(m.state, "installed")

    def test_demo_fleet_seeded(self):
        fleet = self.env["alfa_core_loaner.vehicle"].search([])
        self.assertGreaterEqual(len(fleet), 5, "Demo fleet should include at least 5 loaners")
