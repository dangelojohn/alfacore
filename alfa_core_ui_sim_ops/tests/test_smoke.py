# SPDX-License-Identifier: LGPL-3.0-only
"""Smoke tests for alfa_core_ui_sim_ops."""

from odoo.tests.common import HttpCase, TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_module_installed(self):
        m = self.env["ir.module.module"].search([("name", "=", "alfa_core_ui_sim_ops")])
        self.assertEqual(m.state, "installed")

    def test_mockup_imports(self):
        """The mockup dictionary module should import cleanly."""
        from odoo.addons.alfa_core_ui_sim_ops.data import wireframe_mocks

        self.assertTrue(wireframe_mocks.TECHNICIAN_TABLET)
        self.assertTrue(wireframe_mocks.ADVISOR_COCKPIT)
        self.assertTrue(wireframe_mocks.PRO_REVIEW_QUEUE)
        self.assertTrue(wireframe_mocks.LOANER_GANTT)


@tagged("post_install", "-at_install", "alfacore_sprint_uisim_ops")
class TestOpsSurfaces(HttpCase):
    def test_surfaces_render_unauthenticated_redirect(self):
        """Unauthenticated requests should be redirected, not 500."""
        for surface in ("technician-tablet", "advisor-cockpit", "pro-review-queue", "loaner-gantt"):
            resp = self.url_open(f"/alfacore/sim/ops/{surface}", allow_redirects=False)
            self.assertIn(resp.status_code, (200, 302, 303, 401, 403))

    def test_mockup_param_propagates(self):
        """?mockup=1 should not 500 even without auth."""
        resp = self.url_open(
            "/alfacore/sim/ops/technician-tablet?mockup=1",
            allow_redirects=False,
        )
        self.assertIn(resp.status_code, (200, 302, 303, 401, 403))
