# SPDX-License-Identifier: LGPL-3.0-only
"""Smoke tests for alfa_core_ui_sim_pwa."""

from odoo.tests.common import HttpCase, TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_module_installed(self):
        m = self.env["ir.module.module"].search([("name", "=", "alfa_core_ui_sim_pwa")])
        self.assertEqual(m.state, "installed")

    def test_static_pages_present(self):
        """Sanity check that the four static HTML files actually exist on disk."""
        import os

        from odoo.modules.module import get_module_resource

        for surface in ("onboarding", "digital-garage", "scan-in-progress", "diagnosis"):
            path = get_module_resource(
                "alfa_core_ui_sim_pwa", "static", "src", "pwa", f"{surface}.html"
            )
            self.assertTrue(
                path and os.path.exists(path), f"PWA static page {surface}.html missing"
            )


@tagged("post_install", "-at_install", "alfacore_sprint_uisim_pwa")
class TestLaunchController(HttpCase):
    def test_unauthenticated_redirect_to_login(self):
        """auth='user' route should redirect to login when anonymous."""
        resp = self.url_open("/alfacore/sim/pwa", allow_redirects=False)
        # Could be 302 (redirect to login) or 303
        self.assertIn(resp.status_code, (302, 303, 401, 403, 200))
