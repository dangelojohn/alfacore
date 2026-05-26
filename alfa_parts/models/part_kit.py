# SPDX-License-Identifier: LGPL-3.0-only
"""Service-quote-shaped kit.

Configurator audit §4.8 — kits in AlfaCore are NOT POS-shaped Combos
(which require all components in stock simultaneously). They are service
quote templates: a coherent set of parts + labor for a service blueprint.
"""

from odoo import fields, models


class AlfaPartsKit(models.Model):
    _name = "alfa_parts.part.kit"
    _description = "Service Quote Kit"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    description = fields.Text(translate=True)
    line_ids = fields.One2many("alfa_parts.part.kit.line", "kit_id", string="Components")
    fits_platform_ids = fields.Many2many(
        "alfa_fleet.platform", relation="alfa_parts_kit_platform_rel", string="Fits Platforms"
    )
    fits_engine_ids = fields.Many2many(
        "alfa_fleet.engine", relation="alfa_parts_kit_engine_rel", string="Fits Engines"
    )
    estimated_labor_hours = fields.Float(string="Estimated Labor (hours)")
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Kit code must be unique.",
    )


class AlfaPartsKitLine(models.Model):
    _name = "alfa_parts.part.kit.line"
    _description = "Kit Component"
    _order = "kit_id, sequence, id"

    kit_id = fields.Many2one("alfa_parts.part.kit", required=True, ondelete="cascade")
    part_id = fields.Many2one("alfa_parts.part", required=True)
    quantity = fields.Float(default=1.0, required=True)
    required = fields.Boolean(
        default=True, help="Required parts must be installed. Optional may be configurator-toggled."
    )
    sequence = fields.Integer(default=10)
    notes = fields.Char()
