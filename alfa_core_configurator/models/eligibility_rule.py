# SPDX-License-Identifier: LGPL-3.0-only
"""Eligibility rule — domain-expression-based pruning of configurator options.

Pattern 6 — configuration-as-data. The configurator's available options
are NOT hardcoded in Python; they're filtered by these rule records.
Each rule contains an Odoo domain expression that evaluates against the
configurator session context.

Configurator audit §3.4 — service blueprints publish eligibility rules
that filter what a customer can select given their vehicle, subscription
tier, prior history, and current scan data.
"""

from odoo import fields, models


class AlfaConfiguratorEligibilityRule(models.Model):
    _name = "alfa_core_configurator.eligibility_rule"
    _description = "Configurator Eligibility Rule"
    _order = "blueprint_code, sequence"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    blueprint_code = fields.Char(
        string="Service Blueprint",
        required=True,
        index=True,
        help="Which service blueprint this rule belongs to (e.g. 'oil_change', 'brake_service').",
    )
    domain_expression = fields.Text(
        string="Domain Expression",
        required=True,
        help="Odoo domain expression evaluated against the session context "
        "(the session record is the search target — use field-traversal "
        "syntax through the session's Many2one fields). "
        "Example: [('vehicle_id.year', '>=', 2017), "
        "('subscription_id.plan_id.code', '=', 'pro')]",
    )
    option_value = fields.Char(
        string="Option Value", required=True, help="What this rule enables when matched."
    )
    rule_action = fields.Selection(
        [
            ("show", "Show Option"),
            ("hide", "Hide Option"),
            ("require", "Require Option"),
            ("recommend", "Recommend Default"),
        ],
        required=True,
        default="show",
    )
    explanation = fields.Text(translate=True, help="Why this rule exists. Shown in audit trail.")
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Rule code must be unique.",
    )
