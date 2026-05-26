# SPDX-License-Identifier: LGPL-3.0-only
"""Service quality check.

JTBD §3.2.3 explicitly does NOT extend Odoo's Quality module — Quality is
MRP-bound and assumes manufacturing context. AlfaCore implements a parallel
service-shaped quality_check model.
"""

from odoo import _, fields, models
from odoo.exceptions import UserError


class AlfaServiceQualityCheck(models.Model):
    _name = "alfa_service.quality.check"
    _description = "Service Quality Check"
    _inherit = ["mail.thread"]
    _order = "sale_order_id, sequence, id"

    sale_order_id = fields.Many2one("sale.order", required=True, ondelete="cascade", index=True)
    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    state = fields.Selection(
        [
            ("draft", "Not Started"),
            ("pending", "Pending"),
            ("passed", "Passed"),
            ("failed", "Failed"),
            ("waived", "Waived"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    checked_by_id = fields.Many2one("hr.employee", string="Checked By")
    checked_at = fields.Datetime()
    pass_threshold_note = fields.Text(
        string="Pass Criteria", help="What constitutes a pass. Surfaces in the technician tablet."
    )
    failure_reason = fields.Text(string="Failure Reason")
    sequence = fields.Integer(default=10)

    def action_pass(self):
        for qc in self:
            qc.state = "passed"
            qc.checked_at = fields.Datetime.now()
            qc.checked_by_id = self.env.user.employee_id
            qc.message_post(body=_("Passed by %s.") % self.env.user.name)

    def action_fail(self, reason=None):
        for qc in self:
            if not reason and not qc.failure_reason:
                raise UserError(_("Failure reason required."))
            qc.state = "failed"
            qc.checked_at = fields.Datetime.now()
            qc.checked_by_id = self.env.user.employee_id
            if reason:
                qc.failure_reason = reason
            qc.message_post(body=_("Failed: %s") % (reason or qc.failure_reason))
