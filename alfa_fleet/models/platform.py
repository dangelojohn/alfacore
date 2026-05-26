# SPDX-License-Identifier: LGPL-3.0-only
"""Vehicle platform — Giorgio, 4C, etc."""

from odoo import api, fields, models


class AlfaFleetPlatform(models.Model):
    _name = "alfa_fleet.platform"
    _description = "Vehicle Platform"
    _order = "sequence, name"

    name = fields.Char(string="Platform", required=True, translate=True)
    code = fields.Char(string="Code", required=True)
    sequence = fields.Integer(default=10)
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)
    engine_ids = fields.One2many("alfa_fleet.engine", "platform_id", string="Engines")
    vehicle_count = fields.Integer(compute="_compute_vehicle_count")

    _code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Platform code must be unique.",
    )

    @api.depends()
    def _compute_vehicle_count(self):
        for plat in self:
            plat.vehicle_count = self.env["alfa_fleet.vehicle"].search_count(
                [("platform_id", "=", plat.id)]
            )
