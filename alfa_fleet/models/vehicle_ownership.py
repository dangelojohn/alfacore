# SPDX-License-Identifier: LGPL-3.0-only
"""Vehicle ownership — through-model with role.

Blueprint §4.2.3 — multi-driver households, fleet vehicles, authorized callers.
Resolves the partner↔vehicle relationship as a first-class record with semantic role.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AlfaFleetVehicleOwnership(models.Model):
    _name = "alfa_fleet.vehicle.ownership"
    _description = "Vehicle Ownership"
    _order = "vehicle_id, sequence, id"

    vehicle_id = fields.Many2one(
        "alfa_fleet.vehicle", string="Vehicle", required=True, ondelete="cascade", index=True
    )
    partner_id = fields.Many2one(
        "res.partner", string="Person", required=True, ondelete="restrict", index=True
    )
    role = fields.Selection(
        [
            ("primary_driver", "Primary Driver"),
            ("secondary_driver", "Secondary Driver"),
            ("account_holder", "Account Holder"),
            ("authorized_caller", "Authorized Caller"),
        ],
        required=True,
        default="primary_driver",
    )
    start_date = fields.Date(default=fields.Date.context_today)
    end_date = fields.Date()
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    notes = fields.Text()

    _one_active_primary = models.Constraint(
        "EXCLUDE (vehicle_id WITH =) WHERE (active AND role = 'primary_driver')",
        "Only one active primary driver per vehicle.",
    )

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for own in self:
            if own.end_date and own.start_date and own.end_date < own.start_date:
                raise ValidationError(_("End date cannot precede start date."))
