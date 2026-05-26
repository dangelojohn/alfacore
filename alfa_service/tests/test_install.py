# SPDX-License-Identifier: LGPL-3.0-only
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_installed(self):
        m = self.env["ir.module.module"].search([("name", "=", "alfa_service")])
        self.assertEqual(m.state, "installed")

    def test_bays_seeded(self):
        bays = self.env["alfa_service.bay"].search([])
        self.assertGreaterEqual(len(bays), 4, "Demo bays should be seeded")
