# SPDX-License-Identifier: LGPL-3.0-only
"""Inspection state machine + finding workflow tests."""

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint8")
class TestInspectionWorkflow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vehicle = cls.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7CINS01",
                "year": 2018,
                "model": "Stelvio",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Inspection Customer"})
        cls.so = cls.env["sale.order"].create({"partner_id": cls.partner.id})
        cls.template = cls.env["alfa_core_inspection.template"].create(
            {
                "name": "Test Template",
                "code": "test_template_workflow",
                "version": 1,
            }
        )
        cls.env["alfa_core_inspection.template_item"].create(
            {
                "template_id": cls.template.id,
                "name": "Item 1 — pass/fail",
                "category": "brakes",
                "measurement_type": "pass_fail",
                "is_safety_critical": False,
                "sequence": 10,
            }
        )
        cls.env["alfa_core_inspection.template_item"].create(
            {
                "template_id": cls.template.id,
                "name": "Item 2 — safety critical",
                "category": "safety",
                "measurement_type": "pass_fail",
                "is_safety_critical": True,
                "sequence": 20,
            }
        )
        cls.template.action_publish()

    def _create_inspection(self):
        return self.env["alfa_core_inspection.inspection"].create(
            {
                "template_id": self.template.id,
                "vehicle_id": self.vehicle.id,
                "sale_order_id": self.so.id,
            }
        )

    def test_template_publish_requires_items(self):
        empty = self.env["alfa_core_inspection.template"].create(
            {
                "name": "Empty",
                "code": "empty_template",
            }
        )
        with self.assertRaises(UserError):
            empty.action_publish()

    def test_findings_auto_populate_from_template(self):
        ins = self._create_inspection()
        self.assertEqual(len(ins.finding_ids), 2, "Should have one finding per template item")
        # Findings should be in not_checked state
        for f in ins.finding_ids:
            self.assertEqual(f.state, "not_checked")

    def test_template_version_captured(self):
        ins = self._create_inspection()
        self.assertEqual(ins.template_version, 1)

    def test_start_transitions_to_in_progress(self):
        ins = self._create_inspection()
        ins.action_start()
        self.assertEqual(ins.state, "in_progress")
        self.assertTrue(ins.started_at)

    def test_cannot_submit_with_unchecked_findings(self):
        ins = self._create_inspection()
        ins.action_start()
        with self.assertRaises(UserError):
            ins.action_submit_for_review()

    def test_full_workflow_all_pass(self):
        ins = self._create_inspection()
        ins.action_start()
        for f in ins.finding_ids:
            f.action_mark_pass()
        ins.action_submit_for_review()
        self.assertEqual(ins.state, "pending_review")
        ins.action_send_to_customer()
        # All-pass should auto-approve without customer review
        self.assertEqual(ins.state, "approved")

    def test_workflow_with_warning_routes_to_customer(self):
        ins = self._create_inspection()
        ins.action_start()
        ins.finding_ids[0].action_mark_pass()
        ins.finding_ids[1].action_mark_warn()
        ins.finding_ids[1].remediation_cost = 250.0
        ins.action_submit_for_review()
        ins.action_send_to_customer()
        self.assertEqual(ins.state, "customer_review")

    def test_customer_decision_partial_approval(self):
        ins = self._create_inspection()
        ins.action_start()
        ins.finding_ids[0].action_mark_warn()
        ins.finding_ids[0].remediation_cost = 100.0
        ins.finding_ids[1].action_mark_fail()
        ins.finding_ids[1].remediation_cost = 500.0
        ins.action_submit_for_review()
        ins.action_send_to_customer()
        ins.finding_ids[0].action_customer_approve()
        ins.finding_ids[1].action_customer_decline("Will defer to next service")
        ins.action_record_customer_decision()
        self.assertEqual(ins.state, "partially_approved")
        self.assertEqual(ins.approved_remediation_total, 100.0)

    def test_apply_creates_so_lines(self):
        ins = self._create_inspection()
        ins.action_start()
        ins.finding_ids[0].action_mark_warn()
        ins.finding_ids[0].remediation_cost = 100.0
        ins.finding_ids[1].action_mark_pass()
        ins.action_submit_for_review()
        ins.action_send_to_customer()
        ins.finding_ids[0].action_customer_approve()
        ins.action_record_customer_decision()
        initial_lines = len(self.so.order_line)
        ins.action_apply_to_so()
        self.assertEqual(ins.state, "applied")
        self.assertEqual(len(self.so.order_line), initial_lines + 1)

    def test_safety_critical_fail_flagged(self):
        ins = self._create_inspection()
        ins.action_start()
        ins.finding_ids[0].action_mark_pass()
        ins.finding_ids[1].action_mark_fail()  # the safety-critical one
        ins._compute_finding_stats()
        self.assertTrue(ins.safety_critical_fail)
