# SPDX-License-Identifier: LGPL-3.0-only
"""Smoke tests for alfa_core_ui_sim umbrella."""

from odoo.tests.common import HttpCase, TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_module_installed(self):
        m = self.env["ir.module.module"].search([("name", "=", "alfa_core_ui_sim")])
        self.assertEqual(m.state, "installed")

    def test_journey_surfaces_registered(self):
        """The controller's surface→template map should round-trip."""
        from odoo.addons.alfa_core_ui_sim.controllers.sim_landing import (
            JOURNEY_SURFACES,
        )

        self.assertEqual(len(JOURNEY_SURFACES), 4)
        for tmpl_xmlid in JOURNEY_SURFACES.values():
            tmpl = self.env.ref(tmpl_xmlid, raise_if_not_found=False)
            self.assertTrue(tmpl, f"Template {tmpl_xmlid} not found")


@tagged("post_install", "-at_install", "alfacore_sprint_uisim_umbrella")
class TestLandingAndJourneys(HttpCase):
    def test_landing_renders(self):
        resp = self.url_open("/alfacore/sim", allow_redirects=False)
        self.assertIn(resp.status_code, (200, 302, 303, 401, 403))

    def test_journey_surfaces_render(self):
        for surface in (
            "relationship-tape",
            "blueprint-authoring",
            "configurator",
            "safety-critical",
        ):
            resp = self.url_open(f"/alfacore/sim/journey/{surface}", allow_redirects=False)
            self.assertIn(resp.status_code, (200, 302, 303, 401, 403))

    def test_unknown_surface_404s(self):
        resp = self.url_open("/alfacore/sim/journey/nonexistent", allow_redirects=False)
        self.assertIn(resp.status_code, (302, 303, 401, 403, 404))
