# SPDX-License-Identifier: LGPL-3.0-only
"""Trim level — Sprint, Ti, Veloce, Quadrifoglio, etc."""

from odoo import fields, models


class AlfaFleetTrim(models.Model):
    _name = "alfa_fleet.trim"
    _description = "Vehicle Trim"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    is_performance = fields.Boolean(
        string="Performance Trim", help="Quadrifoglio, GTAm, etc. — drives track-day eligibility."
    )
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Trim code must be unique.",
    )
