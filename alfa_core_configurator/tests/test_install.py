# SPDX-License-Identifier: LGPL-3.0-only
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_installed(self):
        m = self.env["ir.module.module"].search([("name", "=", "alfa_core_configurator")])
        self.assertEqual(m.state, "installed")


@tagged("post_install", "-at_install", "alfacore_sprint7")
class TestSessionTTL(TransactionCase):
    def test_expires_at_30_days(self):
        veh = self.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7CTTL01",
                "year": 2018,
                "model": "Stelvio",
            }
        )
        session = self.env["alfa_core_configurator.session"].create(
            {
                "vehicle_id": veh.id,
                "blueprint_code": "oil_change",
            }
        )
        delta = session.expires_at - session.last_touch_at
        self.assertEqual(delta.days, 30)

    def test_touch_extends_ttl(self):
        veh = self.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7CTTL02",
                "year": 2018,
                "model": "Stelvio",
            }
        )
        session = self.env["alfa_core_configurator.session"].create(
            {
                "vehicle_id": veh.id,
                "blueprint_code": "oil_change",
            }
        )
        old_touch = session.last_touch_at
        session.touch()
        self.assertGreaterEqual(session.last_touch_at, old_touch)
