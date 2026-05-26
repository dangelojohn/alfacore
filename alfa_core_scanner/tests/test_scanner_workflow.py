# SPDX-License-Identifier: LGPL-3.0-only
"""Scanner workflow tests — device pairing, scan session lifecycle, DTC materialization."""

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint5")
class TestScannerWorkflow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Scanner Test Customer"})
        cls.vehicle = cls.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7CSCNX1",
                "year": 2019,
                "model": "Stelvio",
            }
        )

    def test_device_pairing_lifecycle(self):
        """Device state should flow shipped → paired → active."""
        device = self.env["alfa_core_scanner.device"].create(
            {
                "serial_number": "TEST-PAIR-001",
                "model_name": "Vgate iCar Pro",
                "state": "shipped",
            }
        )
        self.assertEqual(device.state, "shipped")
        # Pair to customer + vehicle
        device.write(
            {
                "partner_id": self.partner.id,
                "vehicle_id": self.vehicle.id,
                "state": "paired",
            }
        )
        self.assertEqual(device.state, "paired")
        # Activate
        device.write({"state": "active"})
        self.assertEqual(device.state, "active")

    def test_scan_session_sequence(self):
        """Scan sessions auto-assign AC-SCAN-YYYY-NNNNNN names."""
        device = self.env["alfa_core_scanner.device"].create(
            {
                "serial_number": "TEST-SEQ-001",
                "model_name": "Vgate iCar Pro",
                "partner_id": self.partner.id,
                "vehicle_id": self.vehicle.id,
                "state": "active",
            }
        )
        session = self.env["alfa_core_scanner.scan_session"].create(
            {
                "vehicle_id": self.vehicle.id,
                "device_id": device.id,
                "state": "running",
            }
        )
        self.assertTrue(session.name)
        self.assertIn("AC-SCAN-", session.name)

    def test_dtc_materialization(self):
        """DTCs created against a session should link back and increment dtc_count."""
        device = self.env["alfa_core_scanner.device"].create(
            {
                "serial_number": "TEST-DTC-001",
                "model_name": "Vgate iCar Pro",
                "partner_id": self.partner.id,
                "vehicle_id": self.vehicle.id,
                "state": "active",
            }
        )
        session = self.env["alfa_core_scanner.scan_session"].create(
            {
                "vehicle_id": self.vehicle.id,
                "device_id": device.id,
                "state": "complete",
            }
        )
        self.env["alfa_core_scanner.scan_dtc"].create(
            [
                {
                    "scan_session_id": session.id,
                    "dtc_code": "P0301",
                    "dtc_status": "active",
                    "module_source": "ECM",
                },
                {
                    "scan_session_id": session.id,
                    "dtc_code": "P0507",
                    "dtc_status": "pending",
                    "module_source": "ECM",
                },
            ]
        )
        session.invalidate_recordset()
        self.assertEqual(len(session.dtc_ids), 2)

    def test_demo_data_loaded(self):
        """Demo: John's Vgate device + recent scan session with DTCs."""
        device = self.env.ref("alfa_core_scanner.device_dangelo_vgate", raise_if_not_found=False)
        if not device:
            self.skipTest("Demo data not loaded")
        self.assertEqual(device.state, "active")
        session = self.env.ref("alfa_core_scanner.scan_session_dangelo_recent")
        self.assertEqual(session.state, "uploaded")
        self.assertEqual(len(session.dtc_ids), 2)
        dtc_codes = session.dtc_ids.mapped("dtc_code")
        self.assertIn("P0301", dtc_codes)
        self.assertIn("P0507", dtc_codes)
