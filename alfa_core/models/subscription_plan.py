# SPDX-License-Identifier: LGPL-3.0-only
"""Subscription plan master — Basic/Premium/Pro tier definitions."""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AlfaCoreSubscriptionPlan(models.Model):
    _name = "alfa_core.subscription.plan"
    _description = "AlfaCore Subscription Plan"
    _order = "sequence, id"

    name = fields.Char(
        string="Plan Name",
        required=True,
        translate=True,
        help="Customer-facing name (Basic, Premium, Pro).",
    )
    code = fields.Char(
        string="Code",
        required=True,
        copy=False,
        help="Stable identifier (basic, premium, pro). Used in API and integrations.",
    )
    description = fields.Text(
        string="Description",
        translate=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.template",
        string="Subscription Product",
        domain=[("recurring_invoice", "=", True)],
        help="Links to native Odoo Subscription product for invoicing.",
    )
    sequence = fields.Integer(default=10)
    monthly_price = fields.Float(
        string="Monthly Price (CAD)",
        help="Informational; actual billing on the linked product.",
    )
    annual_price = fields.Float(
        string="Annual Price (CAD)",
        help="Informational; actual billing on the linked product.",
    )
    features = fields.One2many(
        comodel_name="alfa_core.tier.benefit",
        inverse_name="plan_id",
        string="Features",
        help="Structured benefit rows per Configurator audit §2.1.3.",
    )
    inference_zde_default = fields.Boolean(
        string="ZDE Inference Default",
        default=True,
        help="Per Service Plan §8.2 — Basic/Premium default to Ollama-local inference; "
        "Pro tier customers may opt into cloud LLM polish with explicit consent.",
    )
    color = fields.Char(
        string="Brand Color",
        default="#0A3D6B",
        help="Hex color for kanban surface — Industrial Futurism palette.",
    )
    active = fields.Boolean(default=True)
    subscription_count = fields.Integer(
        string="Subscribers",
        compute="_compute_subscription_count",
    )

    _code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Plan code must be unique.",
    )

    @api.depends()
    def _compute_subscription_count(self):
        Subscription = self.env["alfa_core.subscription"]
        for plan in self:
            plan.subscription_count = Subscription.search_count(
                [
                    ("plan_id", "=", plan.id),
                    ("state", "in", ("trial", "active")),
                ]
            )

    @api.constrains("code")
    def _check_code_format(self):
        for plan in self:
            if not plan.code or not plan.code.isidentifier() or not plan.code.islower():
                raise ValidationError(
                    _("Plan code must be a lowercase identifier (a-z, 0-9, underscore).")
                )

    def action_view_subscriptions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Subscriptions"),
            "res_model": "alfa_core.subscription",
            "view_mode": "list,form",
            "domain": [("plan_id", "=", self.id)],
        }
