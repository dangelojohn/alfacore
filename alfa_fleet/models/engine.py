# SPDX-License-Identifier: LGPL-3.0-only
"""Engine taxonomy — GME 2.0T, 2.9 V6, 1750 TBi, etc."""

from odoo import fields, models


class AlfaFleetEngine(models.Model):
    _name = "alfa_fleet.engine"
    _description = "Engine"
    _order = "platform_id, sequence, name"

    name = fields.Char(
        string="Engine", required=True, translate=True, help="Display name (e.g. 'GME 2.0T')."
    )
    code = fields.Char(string="Code", required=True, help="Stable identifier (e.g. 'GME_2_0T').")
    platform_id = fields.Many2one("alfa_fleet.platform", string="Platform", required=True)
    displacement = fields.Char(string="Displacement", help="e.g. 2.0 L")
    configuration = fields.Char(string="Configuration", help="e.g. inline-4, V6")
    horsepower_kw = fields.Float(string="Power (kW)")
    torque_nm = fields.Float(string="Torque (Nm)")
    fuel_type = fields.Selection(
        [
            ("gasoline", "Gasoline"),
            ("diesel", "Diesel"),
            ("hybrid", "Hybrid"),
            ("phev", "Plug-in Hybrid"),
            ("ev", "Electric"),
        ],
        default="gasoline",
        required=True,
    )
    oil_capacity_l = fields.Float(string="Oil Capacity (L)")
    default_oil_spec = fields.Char(string="Default Oil Spec", help="e.g. '5W-40 ACEA C3'")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Engine code must be unique.",
    )
