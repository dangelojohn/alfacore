# SPDX-License-Identifier: LGPL-3.0-only
"""Smoke test for alfa_fleet."""

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_module_installed(self):
        module = self.env["ir.module.module"].search([("name", "=", "alfa_fleet")])
        self.assertEqual(module.state, "installed")

    def test_seed_data_loaded(self):
        giorgio = self.env.ref("alfa_fleet.platform_giorgio", raise_if_not_found=False)
        self.assertTrue(giorgio, "Giorgio platform should be seeded")
        gme = self.env.ref("alfa_fleet.engine_gme_2_0t", raise_if_not_found=False)
        self.assertTrue(gme, "GME 2.0T engine should be seeded")
        self.assertEqual(gme.platform_id, giorgio)
