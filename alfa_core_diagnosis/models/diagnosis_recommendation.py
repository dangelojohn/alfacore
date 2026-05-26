# SPDX-License-Identifier: LGPL-3.0-only
"""Recommended action from a diagnosis."""

from odoo import fields, models


class AlfaDiagnosisRecommendation(models.Model):
    _name = "alfa_core_diagnosis.recommendation"
    _description = "Diagnosis Recommendation"
    _order = "report_id, sequence, id"

    report_id = fields.Many2one(
        "alfa_core_diagnosis.report", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    action_type = fields.Selection(
        [
            ("inspect", "Inspect"),
            ("replace_part", "Replace Part"),
            ("service", "Service Operation"),
            ("test_drive", "Test Drive"),
            ("recall_check", "Check for Recall / TSB"),
            ("monitor", "Monitor"),
            ("do_not_drive", "Do Not Drive"),
        ],
        required=True,
    )
    related_part_id = fields.Many2one("alfa_parts.part", string="Related Part")
    related_kit_id = fields.Many2one("alfa_parts.part.kit", string="Related Kit")
    confidence = fields.Float(default=0.0)
    sequence = fields.Integer(default=10)
