"""
Smoke test for alfa_core_multi_loc.

Verifies that:
1. The module installs cleanly
2. Base models load without error
3. Demo data (if any) imports without error

This is the canonical smoke test per Decision Log §scaffold-Q8. Real test
coverage builds on top of this as models and workflows are implemented.
"""

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    """Canonical install-time smoke test for alfa_core_multi_loc."""

    def test_module_installed(self):
        """Module is registered with Odoo after installation."""
        module = self.env["ir.module.module"].search([("name", "=", "alfa_core_multi_loc")])
        self.assertEqual(len(module), 1, "alfa_core_multi_loc should be registered")
        self.assertEqual(
            module.state, "installed", "alfa_core_multi_loc should be in 'installed' state"
        )

    def test_module_has_manifest(self):
        """Manifest is loadable and contains required fields."""
        module = self.env["ir.module.module"].search([("name", "=", "alfa_core_multi_loc")])
        self.assertTrue(module.shortdesc, "Module should have a short description")
        self.assertTrue(module.summary, "Module should have a summary")
        self.assertEqual(module.license, "LGPL-3", "Module should be LGPL-3 licensed")
