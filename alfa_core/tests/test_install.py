# SPDX-License-Identifier: LGPL-3.0-only
"""Smoke test for alfa_core."""

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_module_installed(self):
        module = self.env["ir.module.module"].search([("name", "=", "alfa_core")])
        self.assertEqual(len(module), 1)
        self.assertEqual(module.state, "installed")
        self.assertEqual(module.license, "LGPL-3")

    def test_sequence_exists(self):
        seq = self.env["ir.sequence"].search([("code", "=", "alfa_core.subscription")])
        self.assertEqual(len(seq), 1, "AlfaCore subscription sequence must be seeded")

    def test_groups_exist(self):
        for ref in ("group_user", "group_advisor", "group_manager", "group_pipeda_officer"):
            group = self.env.ref(f"alfa_core.{ref}", raise_if_not_found=False)
            self.assertTrue(group, f"alfa_core.{ref} should exist after install")
