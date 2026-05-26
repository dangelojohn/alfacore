# SPDX-License-Identifier: LGPL-3.0-only
"""Individual inspection finding — per-item pass/warn/fail with remediation.

Customer-approval-gated: warn/fail findings require explicit customer decision
before becoming SO lines. This is the trust capital for inspection-driven
upselling (which we don't do; we present findings honestly and let the
customer decide).
"""

from odoo import _, fields, models


class AlfaInspectionFinding(models.Model):
    _name = "alfa_core_inspection.finding"
    _description = "Inspection Finding"
    _inherit = ["mail.thread"]
    _order = "inspection_id, sequence, id"

    inspection_id = fields.Many2one(
        "alfa_core_inspection.inspection", required=True, ondelete="cascade", index=True
    )
    template_item_id = fields.Many2one(
        "alfa_core_inspection.template_item", string="From Template Item"
    )
    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    category = fields.Selection(
        [
            ("brakes", "Brakes"),
            ("suspension", "Suspension"),
            ("steering", "Steering"),
            ("drivetrain", "Drivetrain"),
            ("tires", "Tires"),
            ("fluids", "Fluids"),
            ("electrical", "Electrical"),
            ("body", "Body & Exterior"),
            ("interior", "Interior"),
            ("safety", "Safety Systems"),
            ("other", "Other"),
        ]
    )
    measurement_type = fields.Selection(
        [
            ("pass_fail", "Pass / Fail"),
            ("measurement", "Measurement"),
            ("photo", "Photo"),
            ("text", "Free text"),
        ]
    )
    measurement_value = fields.Float()
    measurement_units = fields.Char()
    photo = fields.Image(
        max_width=1920,
        max_height=1080,
        help="Optional photo evidence. Subject to inference_zde flag.",
    )
    note = fields.Text()

    state = fields.Selection(
        [
            ("not_checked", "Not Checked"),
            ("pass", "Pass"),
            ("warn", "Warning"),
            ("fail", "Fail"),
            ("not_applicable", "N/A"),
        ],
        default="not_checked",
        required=True,
        tracking=True,
    )
    is_safety_critical = fields.Boolean()

    # Remediation
    remediation_recommended = fields.Text(
        translate=True, help="What's needed to address this finding."
    )
    remediation_cost = fields.Monetary(
        currency_field="currency_id", help="Estimated cost of the remediation work."
    )
    remediation_part_id = fields.Many2one("alfa_parts.part", string="Related Part")
    remediation_kit_id = fields.Many2one("alfa_parts.part.kit", string="Related Kit")
    remediation_urgency = fields.Selection(
        [
            ("immediate", "Immediate"),
            ("soon", "Within 30 days"),
            ("scheduled", "Next scheduled service"),
            ("monitor", "Monitor only"),
        ],
        default="scheduled",
    )

    # Customer decision (portal-driven; populated via portal write)
    customer_decision = fields.Selection(
        [
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("declined", "Declined"),
            ("defer", "Defer"),
        ],
        default="pending",
        tracking=True,
    )
    customer_decision_at = fields.Datetime()
    customer_decision_note = fields.Text()

    currency_id = fields.Many2one(related="inspection_id.currency_id", store=True)

    # ------------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------------
    def action_mark_pass(self):
        for f in self:
            f.state = "pass"
            f.customer_decision = "approved"  # nothing to decide on a pass

    def action_mark_warn(self, note=None):
        for f in self:
            f.state = "warn"
            if note:
                f.note = note

    def action_mark_fail(self, note=None):
        for f in self:
            f.state = "fail"
            if note:
                f.note = note

    def action_customer_approve(self):
        for f in self:
            f.customer_decision = "approved"
            f.customer_decision_at = fields.Datetime.now()
            f.message_post(body=_("Customer approved this remediation."))

    def action_customer_decline(self, reason=None):
        for f in self:
            f.customer_decision = "declined"
            f.customer_decision_at = fields.Datetime.now()
            if reason:
                f.customer_decision_note = reason
            f.message_post(body=_("Customer declined this remediation."))
