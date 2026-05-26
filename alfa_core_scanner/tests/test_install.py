# SPDX-License-Identifier: LGPL-3.0-only
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_installed(self):
        m = self.env["ir.module.module"].search([("name", "=", "alfa_core_scanner")])
        self.assertEqual(m.state, "installed")

    def test_sequence(self):
        seq = self.env["ir.sequence"].search([("code", "=", "alfa_core_scanner.scan_session")])
        self.assertEqual(len(seq), 1)
