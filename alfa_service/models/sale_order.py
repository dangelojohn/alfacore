# SPDX-License-Identifier: LGPL-3.0-only
"""sale.order extensions — vehicle anchor, service state machine.

Blueprint §8.1 — the state machine that spans nine Odoo modules. AlfaCore
adds states beyond native sale.order's draft/sent/done.

Note: forward references (alfa_scan_session_id, alfa_diagnosis_report_id,
alfa_configurator_session_id) are added when the respective modules ship
in Sprints 5/6/7. They are declared here as Many2one to models that may
not yet exist — Odoo defers the binding until the target model installs.
"""

from odoo import _, api, fields, models

SERVICE_STATES = [
    ("draft", "Draft"),
    ("sent", "Quotation Sent"),
    ("confirmed", "Confirmed"),
    ("parts_ordered", "Parts Ordered"),
    ("parts_ready", "Parts Ready"),
    ("scheduled", "Scheduled"),
    ("in_progress", "In Progress"),
    ("inspection_pending", "Inspection Pending"),
    ("findings_review", "Findings — Customer Review"),
    ("quality_check", "Quality Check"),
    ("ready_for_pickup", "Ready for Pickup"),
    ("picked_up", "Picked Up"),
    ("awaiting_review", "Awaiting Customer Review"),
    ("closed", "Closed"),
    ("cancelled", "Cancelled"),
]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    alfa_vehicle_id = fields.Many2one(
        "alfa_fleet.vehicle",
        string="Vehicle",
        tracking=True,
        index=True,
        help="The vehicle this service order is performed on.",
    )
    alfa_service_state = fields.Selection(
        selection=SERVICE_STATES,
        string="Service State",
        default="draft",
        tracking=True,
        copy=False,
        index=True,
    )
    alfa_bay_id = fields.Many2one(
        "alfa_service.bay",
        string="Service Bay",
        tracking=True,
    )
    alfa_technician_id = fields.Many2one(
        "hr.employee",
        string="Assigned Technician",
        tracking=True,
    )
    alfa_quality_check_ids = fields.One2many(
        "alfa_service.quality.check",
        "sale_order_id",
        string="Quality Checks",
    )
    alfa_quality_check_pending = fields.Boolean(
        compute="_compute_quality_check_pending",
        store=True,
    )

    @api.depends("alfa_quality_check_ids.state")
    def _compute_quality_check_pending(self):
        for so in self:
            so.alfa_quality_check_pending = any(
                qc.state in ("draft", "pending") for qc in so.alfa_quality_check_ids
            )

    def action_advance_service_state(self, new_state):
        """Advance state machine with chatter log (Pattern 9)."""
        for so in self:
            old = so.alfa_service_state
            so.alfa_service_state = new_state
            so.message_post(
                body=_("Service state: %(old)s → %(new)s") % {"old": old, "new": new_state}
            )
