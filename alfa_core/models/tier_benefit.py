# SPDX-License-Identifier: LGPL-3.0-only
"""Tier benefit — structured benefit row per plan (Configurator audit §2.1.3)."""

from odoo import fields, models


class AlfaCoreTierBenefit(models.Model):
    _name = "alfa_core.tier.benefit"
    _description = "AlfaCore Tier Benefit"
    _order = "plan_id, sequence, id"

    plan_id = fields.Many2one(
        comodel_name="alfa_core.subscription.plan",
        string="Plan",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(
        string="Benefit",
        required=True,
        translate=True,
        help="Customer-facing benefit description.",
    )
    benefit_type = fields.Selection(
        selection=[
            ("feature", "Feature"),
            ("limit", "Limit"),
            ("upgrade", "Upgrade"),
        ],
        string="Type",
        default="feature",
        required=True,
    )
    value = fields.Char(
        string="Value",
        translate=True,
        help="The benefit value (e.g., 'Unlimited', '10/month', 'Included').",
    )
    comparison_visible = fields.Boolean(
        string="Show in Comparison",
        default=True,
        help="Display in side-by-side plan comparison view.",
    )
    sequence = fields.Integer(default=10)
