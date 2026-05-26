# SPDX-License-Identifier: LGPL-3.0-only
"""Benefit ledger — audit trail of every recommendation and selection.

Pattern 9 — logging as UI. Every decision the configurator makes — every
option shown or hidden, every recommendation ranked, every selection
applied — gets a ledger row. The customer can ask 'why?' and the answer
is here.
"""

from odoo import fields, models


class AlfaConfiguratorBenefitLedger(models.Model):
    _name = "alfa_core_configurator.benefit_ledger"
    _description = "Configurator Benefit Ledger"
    _order = "session_id, recorded_at desc, id desc"

    session_id = fields.Many2one(
        "alfa_core_configurator.session", required=True, ondelete="cascade", index=True
    )
    entry_type = fields.Selection(
        [
            ("rule_evaluated", "Rule Evaluated"),
            ("option_shown", "Option Shown"),
            ("option_hidden", "Option Hidden"),
            ("recommendation_made", "Recommendation Made"),
            ("option_selected", "Option Selected"),
            ("option_deselected", "Option Deselected"),
            ("benefit_applied", "Benefit Applied"),
            ("override", "Manual Override"),
        ],
        required=True,
    )
    name = fields.Char(required=True)
    explanation = fields.Text(translate=True, help="Plain-English audit trail entry.")
    rule_id = fields.Many2one("alfa_core_configurator.eligibility_rule")
    related_signal_id = fields.Many2one("alfa_core_configurator.signal")
    related_value = fields.Char()
    actor_user_id = fields.Many2one("res.users", default=lambda s: s.env.user)
    recorded_at = fields.Datetime(default=fields.Datetime.now, required=True)
