# SPDX-License-Identifier: LGPL-3.0-only
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_installed(self):
        m = self.env["ir.module.module"].search([("name", "=", "alfa_core_cuore")])
        self.assertEqual(m.state, "installed")
        self.assertEqual(
            len(self.env["ir.sequence"].search([("code", "=", "alfa.cuore.bundle")])), 1
        )
        tmpl = self.env.ref("alfa_core_cuore.template_cuore_plan")
        self.assertEqual((tmpl.state, tmpl.item_count), ("published", 1))
