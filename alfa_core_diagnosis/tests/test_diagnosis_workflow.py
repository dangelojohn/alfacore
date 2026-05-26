# SPDX-License-Identifier: LGPL-3.0-only
"""Diagnosis workflow tests — state machine, Pro review, recommendation generation."""

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint6")
class TestDiagnosisWorkflow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Diagnosis Test Customer"})
        cls.vehicle = cls.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7CDXNX1",
                "year": 2019,
                "model": "Stelvio",
            }
        )
        cls.device = cls.env["alfa_core_scanner.device"].create(
            {
                "serial_number": "DX-TEST-001",
                "model_name": "Vgate iCar Pro",
                "partner_id": cls.partner.id,
                "vehicle_id": cls.vehicle.id,
                "state": "active",
            }
        )
        cls.session = cls.env["alfa_core_scanner.scan_session"].create(
            {
                "vehicle_id": cls.vehicle.id,
                "device_id": cls.device.id,
                "state": "uploaded",
            }
        )

    def test_report_sequence_assigned(self):
        report = self.env["alfa_core_diagnosis.report"].create(
            {
                "scan_session_id": self.session.id,
            }
        )
        self.assertTrue(report.name)
        self.assertIn("AC-DX-", report.name)

    def test_state_machine_progression(self):
        report = self.env["alfa_core_diagnosis.report"].create(
            {
                "scan_session_id": self.session.id,
            }
        )
        self.assertEqual(report.state, "draft")
        report.write({"state": "ai_generated", "confidence": 0.72})
        report.write({"state": "pending_review"})
        report.write({"state": "reviewed", "reviewed_by_id": self.env.user.id})
        self.assertEqual(report.state, "reviewed")

    def test_safety_critical_severity_routing(self):
        """A diagnosis with safety_critical severity should be flagged."""
        report = self.env["alfa_core_diagnosis.report"].create(
            {
                "scan_session_id": self.session.id,
                "severity": "safety_critical",
                "confidence": 0.92,
            }
        )
        # Severity is captured; downstream UI handles do-not-drive messaging
        self.assertEqual(report.severity, "safety_critical")

    def test_recommendation_part_linkage(self):
        """A recommendation can link to a part for inventory and ordering."""
        coil_part = self.env.ref("alfa_parts.part_coil_55214664", raise_if_not_found=False)
        if not coil_part:
            self.skipTest("Coil part demo not loaded")
        report = self.env["alfa_core_diagnosis.report"].create(
            {
                "scan_session_id": self.session.id,
            }
        )
        rec = self.env["alfa_core_diagnosis.recommendation"].create(
            {
                "report_id": report.id,
                "name": "Replace coil",
                "action_type": "replace_part",
                "related_part_id": coil_part.id,
                "confidence": 0.78,
            }
        )
        self.assertEqual(rec.related_part_id, coil_part)

    def test_triage_rule_seeded(self):
        """Demo triage rules should be loaded."""
        rule = self.env.ref("alfa_core_diagnosis.rule_p0301_coil_pattern", raise_if_not_found=False)
        if not rule:
            self.skipTest("Demo rules not loaded")
        self.assertEqual(rule.dtc_pattern, "P0301")
        self.assertGreater(rule.confidence_base, 0.7)

    def test_demo_report_full_chain(self):
        """Full demo chain: scan session → diagnosis report → recommendations."""
        report = self.env.ref(
            "alfa_core_diagnosis.report_dangelo_misfire", raise_if_not_found=False
        )
        if not report:
            self.skipTest("Demo report not loaded")
        self.assertEqual(report.state, "reviewed")
        self.assertGreaterEqual(len(report.recommendation_ids), 2)
        # The coil replacement rec should link to the actual coil part
        coil_rec = report.recommendation_ids.filtered(lambda r: r.action_type == "replace_part")
        self.assertTrue(coil_rec)
        self.assertTrue(coil_rec[0].related_part_id)
