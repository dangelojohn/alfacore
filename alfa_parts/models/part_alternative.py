# SPDX-License-Identifier: LGPL-3.0-only
"""Aftermarket alternative with grade and rationale.

JTBD §2.8 — customers need transparent guidance on when an alternative is
acceptable vs. when only OEM should be used. This is the trust capital for
parts recommendations.
"""

from odoo import fields, models


class AlfaPartsAlternative(models.Model):
    _name = "alfa_parts.part.alternative"
    _description = "Part Alternative"
    _order = "oem_part_id, grade, sequence"

    oem_part_id = fields.Many2one(
        "alfa_parts.part", string="OEM Part", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(string="Alternative Part", required=True, translate=True)
    part_number = fields.Char(string="Part Number")
    manufacturer = fields.Char(required=True, help="e.g. NGK, Brembo, FCP Euro house brand")
    grade = fields.Selection(
        [
            ("safe", "Safe Equivalent"),
            ("interim", "Interim — Acceptable Short-term"),
            ("not_recommended", "Not Recommended"),
        ],
        required=True,
        default="safe",
        help="Pattern 10 — honest grading. Safe = no compromise; "
        "Interim = acceptable until OEM available; "
        "Not Recommended = installation discouraged.",
    )
    rationale = fields.Text(
        required=True, translate=True, help="Why this grade. Source-cited evaluation."
    )
    source_reference = fields.Char(
        string="Source", help="Diagnosis ID, TSB reference, or technician evaluation note."
    )
    price_savings_pct = fields.Float(string="Typical Savings (%)")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
