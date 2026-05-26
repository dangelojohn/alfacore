# SPDX-License-Identifier: LGPL-3.0-only
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_installed(self):
        m = self.env["ir.module.module"].search([("name", "=", "alfa_core_diagnosis")])
        self.assertEqual(m.state, "installed")

    def test_dtc_seed_loaded(self):
        dtc = self.env.ref("alfa_core_diagnosis.dtc_P0301", raise_if_not_found=False)
        self.assertTrue(dtc, "P0301 should be seeded")

    def test_safety_critical_compute(self):
        dtc = self.env.ref("alfa_core_diagnosis.dtc_C0561")
        self.assertTrue(dtc.is_safety_critical)
