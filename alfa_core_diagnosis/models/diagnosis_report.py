# SPDX-License-Identifier: LGPL-3.0-only
"""Diagnosis report — vehicle-anchored, scan-session-derived.

Pattern 11 — per-record privacy disposition. The report's inference_zde
flag derives from the scan_session and ultimately from the subscription.
"""

from odoo import _, api, fields, models


class AlfaDiagnosisReport(models.Model):
    _name = "alfa_core_diagnosis.report"
    _description = "Diagnosis Report"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"
    _rec_name = "name"

    name = fields.Char(required=True, copy=False, readonly=True, default=lambda s: _("New"))
    scan_session_id = fields.Many2one(
        "alfa_core_scanner.scan_session", required=True, ondelete="restrict", index=True
    )
    vehicle_id = fields.Many2one(related="scan_session_id.vehicle_id", store=True, index=True)
    partner_id = fields.Many2one(related="vehicle_id.primary_owner_id", store=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("ai_generated", "AI-Generated"),
            ("pending_review", "Pending Pro Review"),
            ("reviewed", "Reviewed"),
            ("delivered", "Delivered to Customer"),
            ("disputed", "Disputed"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )

    confidence = fields.Float(
        string="Confidence", default=0.0, help="Aggregate confidence 0.0-1.0."
    )
    severity = fields.Selection(
        [
            ("info", "Info"),
            ("warn", "Warning"),
            ("severe", "Severe"),
            ("safety_critical", "Safety-Critical"),
        ],
        default="warn",
        tracking=True,
    )
    inference_zde = fields.Boolean(default=True)
    summary = fields.Text(translate=True, help="Customer-facing plain-English summary.")
    technical_summary = fields.Text(string="Technical Summary", help="Internal technician-facing.")
    recommendation_ids = fields.One2many(
        "alfa_core_diagnosis.recommendation", "report_id", string="Recommendations"
    )
    # `res.users` rather than `hr.employee` — keeps alfa_core_diagnosis free
    # of the `hr` dependency. A reviewer is whichever Odoo user marked the
    # report reviewed; tie back to an employee via user.employee_id if the
    # hr module is installed.
    reviewed_by_id = fields.Many2one("res.users", string="Pro Reviewer")
    reviewed_at = fields.Datetime()
    review_notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "alfa_core_diagnosis.report"
                ) or _("New")
        return super().create(vals_list)
