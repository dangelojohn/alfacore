# SPDX-License-Identifier: LGPL-3.0-only
"""Per-vehicle preferences — fluid, parts, tire, alignment specs.

JTBD §2.5 — the moat. Customer never has to repeat their fluid spec, brand,
or tire preference. Service Plan §5.2.
"""

from odoo import fields, models


class AlfaFleetVehiclePreference(models.Model):
    _name = "alfa_fleet.vehicle.preference"
    _description = "Vehicle Preference"
    _order = "vehicle_id, sequence, id"

    vehicle_id = fields.Many2one(
        "alfa_fleet.vehicle", required=True, ondelete="cascade", index=True
    )
    category = fields.Selection(
        [
            ("oil", "Engine Oil"),
            ("brake_fluid", "Brake Fluid"),
            ("coolant", "Coolant"),
            ("transmission_fluid", "Transmission Fluid"),
            ("transfer_case", "Transfer Case Fluid"),
            ("differential", "Differential Fluid"),
            ("washer_fluid", "Washer Fluid"),
            ("tire", "Tires"),
            ("alignment", "Alignment Spec"),
            ("battery", "Battery"),
            ("other", "Other"),
        ],
        required=True,
    )
    name = fields.Char(
        string="Preference",
        required=True,
        help="e.g. '5W-40 Selenia K Pure Energy'",
    )
    spec = fields.Text(
        string="Specification", help="Detailed spec (e.g. 'ACEA C3, MOPAR MS-12991')"
    )
    brand_preference = fields.Char(string="Brand Preference")
    set_by_id = fields.Many2one(
        "res.partner", string="Set By", help="Customer or advisor who established this preference."
    )
    set_date = fields.Date(default=fields.Date.context_today)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    notes = fields.Text()
