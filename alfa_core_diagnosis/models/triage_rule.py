# SPDX-License-Identifier: LGPL-3.0-only
"""Rule-based diagnosis triage.

Pattern 6 — configuration-as-data. Diagnosis rules are records, not Python
branches. Service Plan §7.3.
"""

from odoo import fields, models


class AlfaDiagnosisTriageRule(models.Model):
    _name = "alfa_core_diagnosis.triage_rule"
    _description = "Diagnosis Triage Rule"
    _order = "sequence, priority desc, id"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, help="Stable identifier for the rule.")
    sequence = fields.Integer(default=10)
    priority = fields.Integer(default=50, help="Higher = evaluated first within the same sequence.")
    dtc_pattern = fields.Char(
        string="DTC Pattern", help="DTC code or pattern (e.g. 'P030[0-9]' for any misfire)."
    )
    pid_condition = fields.Char(
        string="PID Condition",
        help="Optional PID-based condition, e.g. 'coolant_temp > 110'. "
        "Evaluated by the diagnosis engine.",
    )
    recommended_action = fields.Text(string="Recommended Action", translate=True, required=True)
    confidence_base = fields.Float(
        string="Base Confidence",
        default=0.7,
        help="0.0-1.0. Adjusted by signal corroboration in the engine.",
    )
    severity = fields.Selection(
        [
            ("info", "Info"),
            ("warn", "Warning"),
            ("severe", "Severe"),
            ("safety_critical", "Safety-Critical"),
        ],
        default="warn",
        required=True,
    )
    fits_platform_ids = fields.Many2many(
        "alfa_fleet.platform", relation="alfa_diagnosis_rule_platform_rel", string="Platforms"
    )
    fits_engine_ids = fields.Many2many(
        "alfa_fleet.engine", relation="alfa_diagnosis_rule_engine_rel", string="Engines"
    )
    active = fields.Boolean(default=True)
