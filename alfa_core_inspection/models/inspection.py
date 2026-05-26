# SPDX-License-Identifier: LGPL-3.0-only
"""Inspection instance — vehicle-anchored, technician-performed.

Pattern 4 — per-vehicle isolation. Every inspection has exactly one vehicle.
Pattern 9 — state transitions log to chatter.
Pattern 11 — inference_zde inherited from the originating SO/subscription.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AlfaInspection(models.Model):
    _name = "alfa_core_inspection.inspection"
    _description = "Vehicle Inspection"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"
    _rec_name = "name"

    name = fields.Char(required=True, copy=False, readonly=True, default=lambda s: _("New"))
    template_id = fields.Many2one(
        "alfa_core_inspection.template",
        string="Template",
        required=True,
        tracking=True,
        domain=[("state", "=", "published")],
    )
    template_version = fields.Integer(
        string="Template Version", help="Captured at creation. Survives template retirement."
    )
    vehicle_id = fields.Many2one("alfa_fleet.vehicle", required=True, tracking=True, index=True)
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Service Order",
        tracking=True,
        index=True,
        help="The SO this inspection was performed against.",
    )
    technician_id = fields.Many2one("hr.employee", string="Technician", tracking=True)
    bay_id = fields.Many2one("alfa_service.bay", string="Bay")

    started_at = fields.Datetime()
    completed_at = fields.Datetime()
    customer_reviewed_at = fields.Datetime()

    finding_ids = fields.One2many(
        "alfa_core_inspection.finding", "inspection_id", string="Findings"
    )
    finding_count = fields.Integer(compute="_compute_finding_stats", store=True)
    finding_pass_count = fields.Integer(compute="_compute_finding_stats", store=True)
    finding_warn_count = fields.Integer(compute="_compute_finding_stats", store=True)
    finding_fail_count = fields.Integer(compute="_compute_finding_stats", store=True)
    safety_critical_fail = fields.Boolean(compute="_compute_finding_stats", store=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("pending_review", "Pending Advisor Review"),
            ("customer_review", "Customer Review"),
            ("approved", "Approved"),
            ("partially_approved", "Partially Approved"),
            ("declined", "Declined"),
            ("applied", "Applied to SO"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )

    estimated_remediation_total = fields.Monetary(
        compute="_compute_remediation_total", store=True, currency_field="currency_id"
    )
    approved_remediation_total = fields.Monetary(
        compute="_compute_remediation_total", store=True, currency_field="currency_id"
    )
    currency_id = fields.Many2one(
        "res.currency", default=lambda s: s.env.company.currency_id, required=True
    )
    inference_zde = fields.Boolean(
        default=True, help="If True, photos and notes stay on local infra only."
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "alfa_core_inspection.inspection"
                ) or _("New")
            # Snapshot template version at creation
            if vals.get("template_id") and "template_version" not in vals:
                tmpl = self.env["alfa_core_inspection.template"].browse(vals["template_id"])
                vals["template_version"] = tmpl.version
        records = super().create(vals_list)
        # Auto-populate findings from template items
        for rec in records:
            if rec.template_id and not rec.finding_ids:
                rec._instantiate_findings_from_template()
        return records

    def _instantiate_findings_from_template(self):
        """Create one finding per template item, default state not_checked."""
        self.ensure_one()
        Finding = self.env["alfa_core_inspection.finding"]
        findings_vals = []
        for item in self.template_id.item_ids:
            findings_vals.append(
                {
                    "inspection_id": self.id,
                    "template_item_id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "measurement_type": item.measurement_type,
                    "measurement_units": item.measurement_units,
                    "is_safety_critical": item.is_safety_critical,
                    "sequence": item.sequence,
                    "state": "not_checked",
                }
            )
        if findings_vals:
            Finding.create(findings_vals)

    @api.depends("finding_ids.state", "finding_ids.is_safety_critical")
    def _compute_finding_stats(self):
        for ins in self:
            ins.finding_count = len(ins.finding_ids)
            ins.finding_pass_count = len(ins.finding_ids.filtered(lambda f: f.state == "pass"))
            ins.finding_warn_count = len(ins.finding_ids.filtered(lambda f: f.state == "warn"))
            ins.finding_fail_count = len(ins.finding_ids.filtered(lambda f: f.state == "fail"))
            ins.safety_critical_fail = any(
                f.state == "fail" and f.is_safety_critical for f in ins.finding_ids
            )

    @api.depends("finding_ids.remediation_cost", "finding_ids.customer_decision")
    def _compute_remediation_total(self):
        for ins in self:
            ins.estimated_remediation_total = sum(
                f.remediation_cost for f in ins.finding_ids if f.state in ("warn", "fail")
            )
            ins.approved_remediation_total = sum(
                f.remediation_cost for f in ins.finding_ids if f.customer_decision == "approved"
            )

    # ------------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------------
    def action_start(self):
        for ins in self:
            if ins.state != "draft":
                raise UserError(_("Can only start a draft inspection."))
            ins.state = "in_progress"
            ins.started_at = fields.Datetime.now()
            ins.message_post(body=_("Inspection started by %s.") % self.env.user.name)

    def action_submit_for_review(self):
        for ins in self:
            if ins.state != "in_progress":
                raise UserError(_("Can only submit an in-progress inspection."))
            unchecked = ins.finding_ids.filtered(lambda f: f.state == "not_checked")
            if unchecked:
                raise UserError(
                    _("%d finding(s) still unchecked. Complete all items before submitting.")
                    % len(unchecked)
                )
            ins.state = "pending_review"
            ins.completed_at = fields.Datetime.now()
            ins.message_post(body=_("Inspection submitted for advisor review."))

    def action_send_to_customer(self):
        for ins in self:
            if ins.state != "pending_review":
                raise UserError(_("Inspection must be in pending review."))
            if ins.finding_warn_count == 0 and ins.finding_fail_count == 0:
                # All-pass — skip customer review
                ins.state = "approved"
                ins.message_post(body=_("All findings passed. Auto-approved."))
                continue
            ins.state = "customer_review"
            ins.message_post(
                body=_("Sent to customer for review: %d warning(s), %d failure(s).")
                % (ins.finding_warn_count, ins.finding_fail_count)
            )

    def action_record_customer_decision(self):
        """Called after customer has decided on each finding via the portal."""
        for ins in self:
            if ins.state != "customer_review":
                raise UserError(_("Inspection must be in customer review."))
            decided = ins.finding_ids.filtered(lambda f: f.state in ("warn", "fail"))
            approved = decided.filtered(lambda f: f.customer_decision == "approved")
            declined = decided.filtered(lambda f: f.customer_decision == "declined")
            pending = decided.filtered(lambda f: f.customer_decision == "pending")
            if pending:
                raise UserError(
                    _("%d remediation(s) still pending customer decision.") % len(pending)
                )
            if approved and declined:
                ins.state = "partially_approved"
            elif approved:
                ins.state = "approved"
            else:
                ins.state = "declined"
            ins.customer_reviewed_at = fields.Datetime.now()
            ins.message_post(
                body=_("Customer reviewed: %d approved, %d declined.")
                % (len(approved), len(declined))
            )

    def action_apply_to_so(self):
        """Push approved findings as SO lines.

        Each approved finding becomes a sale.order.line with the remediation cost
        and a reference back to the inspection finding for audit trail.
        """
        for ins in self:
            if ins.state not in ("approved", "partially_approved"):
                raise UserError(_("Inspection must be approved (in full or part)."))
            if not ins.sale_order_id:
                raise UserError(_("No SO linked to this inspection."))
            approved_findings = ins.finding_ids.filtered(
                lambda f: f.customer_decision == "approved"
            )
            for finding in approved_findings:
                self.env["sale.order.line"].create(
                    {
                        "order_id": ins.sale_order_id.id,
                        "name": _("Inspection finding: %s") % finding.name,
                        "price_unit": finding.remediation_cost,
                        "product_uom_qty": 1,
                    }
                )
            ins.state = "applied"
            ins.message_post(
                body=_("%d approved finding(s) applied to %s as SO lines.")
                % (len(approved_findings), ins.sale_order_id.name)
            )

    def action_cancel(self):
        for ins in self:
            ins.state = "cancelled"
            ins.message_post(body=_("Inspection cancelled by %s.") % self.env.user.name)
