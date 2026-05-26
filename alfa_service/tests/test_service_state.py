# SPDX-License-Identifier: LGPL-3.0-only
"""Service state machine tests."""

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint4")
class TestServiceState(TransactionCase):
    def test_default_state_is_draft(self):
        partner = self.env["res.partner"].create({"name": "SO Customer"})
        so = self.env["sale.order"].create({"partner_id": partner.id})
        self.assertEqual(so.alfa_service_state, "draft")

    def test_state_transition_logs_chatter(self):
        partner = self.env["res.partner"].create({"name": "SO Customer 2"})
        so = self.env["sale.order"].create({"partner_id": partner.id})
        so.action_advance_service_state("confirmed")
        self.assertEqual(so.alfa_service_state, "confirmed")
        self.assertTrue(any("draft" in m.body and "confirmed" in m.body for m in so.message_ids))

    def test_quality_check_pending_compute(self):
        partner = self.env["res.partner"].create({"name": "QC Customer"})
        so = self.env["sale.order"].create({"partner_id": partner.id})
        qc = self.env["alfa_service.quality.check"].create(
            {
                "sale_order_id": so.id,
                "name": "Torque verify",
            }
        )
        so._compute_quality_check_pending()
        self.assertTrue(so.alfa_quality_check_pending)
        qc.action_pass()
        so._compute_quality_check_pending()
        self.assertFalse(so.alfa_quality_check_pending)
