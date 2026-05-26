# SPDX-License-Identifier: LGPL-3.0-only
"""Customer subscription instance with state machine."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AlfaCoreSubscription(models.Model):
    _name = "alfa_core.subscription"
    _description = "AlfaCore Subscription"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"
    _rec_name = "name"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        required=True,
        tracking=True,
        index=True,
    )
    plan_id = fields.Many2one(
        comodel_name="alfa_core.subscription.plan",
        string="Plan",
        required=True,
        tracking=True,
    )
    start_date = fields.Date(
        string="Start Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    end_date = fields.Date(
        string="End Date",
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("trial", "Trial"),
            ("active", "Active"),
            ("past_due", "Past Due"),
            ("cancelled", "Cancelled"),
            ("expired", "Expired"),
        ],
        string="Status",
        default="trial",
        required=True,
        tracking=True,
        index=True,
    )
    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Originating Order",
        ondelete="set null",
    )
    # NOTE: vehicle_ids M2M will be added in Sprint 2 (alfa_fleet) when
    # alfa_fleet.vehicle exists. This is the deferred relationship from
    # the Sprint 1 brief — closed in Sprint 2.
    inference_zde = fields.Boolean(
        string="ZDE Inference",
        default=True,
        tracking=True,
        help="Per-record privacy disposition (Pattern 11). "
        "True = Ollama-local only; False = cloud LLM polish allowed.",
    )
    notes = fields.Text(string="Internal Notes")
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                seq = self.env["ir.sequence"].next_by_code("alfa_core.subscription")
                vals["name"] = seq or _("New")
            # Inherit plan's ZDE default unless explicitly set
            if "inference_zde" not in vals and vals.get("plan_id"):
                plan = self.env["alfa_core.subscription.plan"].browse(vals["plan_id"])
                vals["inference_zde"] = plan.inference_zde_default
        return super().create(vals_list)

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for sub in self:
            if sub.end_date and sub.start_date and sub.end_date < sub.start_date:
                raise ValidationError(_("End date cannot precede start date."))

    # ------------------------------------------------------------------------
    # State transitions — log to chatter (Pattern 9: logging as UI)
    # ------------------------------------------------------------------------
    def action_activate(self):
        for sub in self:
            if sub.state not in ("trial", "past_due"):
                raise UserError(_("Cannot activate from state '%s'.") % sub.state)
            sub.state = "active"
            sub.message_post(body=_("Subscription activated."))

    def action_mark_past_due(self):
        for sub in self:
            if sub.state != "active":
                raise UserError(_("Cannot mark past due from state '%s'.") % sub.state)
            sub.state = "past_due"
            sub.message_post(body=_("Subscription marked past due."))

    def action_cancel(self):
        for sub in self:
            if sub.state == "cancelled":
                raise UserError(_("Already cancelled."))
            sub.state = "cancelled"
            sub.end_date = fields.Date.context_today(self)
            sub.message_post(body=_("Subscription cancelled by %s.", self.env.user.name))

    def action_expire(self):
        for sub in self:
            if sub.state in ("cancelled", "expired"):
                continue
            sub.state = "expired"
            sub.message_post(body=_("Subscription expired."))
