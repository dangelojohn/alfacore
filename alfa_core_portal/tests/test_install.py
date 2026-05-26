# SPDX-License-Identifier: LGPL-3.0-only
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_installed(self):
        m = self.env["ir.module.module"].search([("name", "=", "alfa_core_portal")])
        self.assertEqual(m.state, "installed")

    def test_ir_rules_loaded(self):
        rules = self.env["ir.rule"].search([("name", "ilike", "Portal:")])
        self.assertGreaterEqual(len(rules), 5, "Should have at least 5 portal row-level rules")
