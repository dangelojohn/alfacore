# SPDX-License-Identifier: LGPL-3.0-only
"""Vehicle model tests — VIN validation, mileage tracking, display name."""

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint2")
class TestVehicle(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.platform = cls.env["alfa_fleet.platform"].create(
            {
                "name": "Test Platform",
                "code": "test_plat",
            }
        )
        cls.engine = cls.env["alfa_fleet.engine"].create(
            {
                "name": "Test Engine",
                "code": "test_eng",
                "platform_id": cls.platform.id,
            }
        )

    def test_valid_vin_accepted(self):
        veh = self.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7C12345",
                "year": 2018,
                "model": "Stelvio",
            }
        )
        self.assertEqual(veh.vin, "ZASFAKBN3J7C12345")

    def test_vin_uppercased(self):
        veh = self.env["alfa_fleet.vehicle"].create(
            {
                "vin": "zasfakbn3j7c12346",
                "year": 2018,
                "model": "Stelvio",
            }
        )
        self.assertEqual(veh.vin, "ZASFAKBN3J7C12346")

    def test_invalid_vin_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["alfa_fleet.vehicle"].create(
                {
                    "vin": "TOO_SHORT",  # not 17 chars
                    "year": 2018,
                    "model": "Stelvio",
                }
            )

    def test_vin_with_io_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["alfa_fleet.vehicle"].create(
                {
                    "vin": "ZASFAKBN3J7CIO345",  # contains I and O
                    "year": 2018,
                    "model": "Stelvio",
                }
            )

    def test_duplicate_vin_rejected(self):
        self.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7C99991",
                "year": 2018,
                "model": "Stelvio",
            }
        )
        with self.assertRaises(Exception):
            self.env["alfa_fleet.vehicle"].create(
                {
                    "vin": "ZASFAKBN3J7C99991",
                    "year": 2019,
                    "model": "Stelvio",
                }
            )

    def test_year_range_validated(self):
        with self.assertRaises(ValidationError):
            self.env["alfa_fleet.vehicle"].create(
                {
                    "vin": "ZASFAKBN3J7C99992",
                    "year": 1900,
                    "model": "Stelvio",
                }
            )

    def test_negative_mileage_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["alfa_fleet.vehicle"].create(
                {
                    "vin": "ZASFAKBN3J7C99993",
                    "year": 2018,
                    "model": "Stelvio",
                    "last_mileage_km": -100,
                }
            )

    def test_mileage_write_stamps_date(self):
        veh = self.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7C99994",
                "year": 2018,
                "model": "Stelvio",
            }
        )
        self.assertFalse(veh.last_mileage_date)
        veh.last_mileage_km = 50000
        self.assertTrue(veh.last_mileage_date)

    def test_display_name_composition(self):
        trim = self.env["alfa_fleet.trim"].create({"name": "Ti", "code": "ti_test"})
        veh = self.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7C99995",
                "year": 2018,
                "model": "Stelvio",
                "trim_id": trim.id,
            }
        )
        self.assertEqual(veh.display_name, "2018 Stelvio Ti")
