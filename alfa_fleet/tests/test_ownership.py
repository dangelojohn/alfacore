# SPDX-License-Identifier: LGPL-3.0-only
"""Vehicle ownership through-model tests."""

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint2")
class TestOwnership(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Owner"})
        cls.partner2 = cls.env["res.partner"].create({"name": "Test Secondary"})
        cls.vehicle = cls.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7C88881",
                "year": 2018,
                "model": "Stelvio",
            }
        )

    def test_primary_owner_compute(self):
        self.env["alfa_fleet.vehicle.ownership"].create(
            {
                "vehicle_id": self.vehicle.id,
                "partner_id": self.partner.id,
                "role": "primary_driver",
            }
        )
        self.vehicle._compute_primary_owner()
        self.assertEqual(self.vehicle.primary_owner_id, self.partner)

    def test_multiple_roles(self):
        self.env["alfa_fleet.vehicle.ownership"].create(
            {
                "vehicle_id": self.vehicle.id,
                "partner_id": self.partner.id,
                "role": "primary_driver",
            }
        )
        self.env["alfa_fleet.vehicle.ownership"].create(
            {
                "vehicle_id": self.vehicle.id,
                "partner_id": self.partner2.id,
                "role": "secondary_driver",
            }
        )
        self.assertEqual(len(self.vehicle.ownership_ids), 2)
