# SPDX-License-Identifier: LGPL-3.0-only
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_installed(self):
        m = self.env["ir.module.module"].search([("name", "=", "alfa_core_inspection")])
        self.assertEqual(m.state, "installed")

    def test_sequence_exists(self):
        seq = self.env["ir.sequence"].search([("code", "=", "alfa_core_inspection.inspection")])
        self.assertEqual(len(seq), 1)

    def test_demo_templates_loaded(self):
        spring = self.env.ref(
            "alfa_core_inspection.template_spring_readiness", raise_if_not_found=False
        )
        self.assertTrue(spring, "Spring readiness template should be seeded")
        self.assertEqual(spring.state, "published")
        self.assertGreaterEqual(spring.item_count, 8)
