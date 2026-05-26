# SPDX-License-Identifier: LGPL-3.0-only
"""Loaner vehicle — shop-owned, allocated temporarily to customers.

Distinct from alfa_fleet.vehicle (customer-owned). Loaner fleet has its
own lifecycle: acquisition, in-rotation, maintenance, retirement.

Per Service Plan §6.4 — Premium and Pro tiers include loaner allocation
during service. The fleet is internally administered.
"""

from odoo import api, fields, models


class AlfaLoanerVehicle(models.Model):
    _name = "alfa_core_loaner.vehicle"
    _description = "Loaner Vehicle"
    _inherit = ["mail.thread"]
    _order = "sequence, name"

    name = fields.Char(
        string="Fleet Name",
        required=True,
        tracking=True,
        help="Internal name, e.g. 'Loaner Stelvio #3'.",
    )
    vin = fields.Char(size=17, copy=False, tracking=True, index=True)
    license_plate = fields.Char(string="License Plate", required=True, copy=False)
    year = fields.Integer(required=True)
    model_name = fields.Char(
        string="Model", required=True, help="e.g. 'Stelvio Ti', 'Giulia Sprint'."
    )
    platform_id = fields.Many2one("alfa_fleet.platform", string="Platform")
    trim_id = fields.Many2one("alfa_fleet.trim", string="Trim")
    tier_eligibility = fields.Selection(
        [
            ("basic_plus", "Basic+ (entry loaners)"),
            ("premium", "Premium (Stelvio/Giulia)"),
            ("pro", "Pro (Quadrifoglio / 4C)"),
        ],
        default="premium",
        required=True,
        help="Which subscription tier this loaner is reserved for. Pro loaners "
        "are exclusive; Premium loaners can be allocated to any tier.",
    )
    seats = fields.Integer(default=5)
    color = fields.Char()
    current_mileage_km = fields.Integer(string="Current Mileage (km)")
    location_id = fields.Many2one(
        "res.partner", string="Home Location", domain=[("is_company", "=", True)]
    )
    sequence = fields.Integer(default=10)

    state = fields.Selection(
        [
            ("available", "Available"),
            ("allocated", "Allocated"),
            ("maintenance", "In Maintenance"),
            ("retired", "Retired"),
        ],
        default="available",
        required=True,
        tracking=True,
        index=True,
    )

    active = fields.Boolean(default=True)

    allocation_ids = fields.One2many(
        "alfa_core_loaner.allocation", "loaner_vehicle_id", string="Allocation History"
    )
    current_allocation_id = fields.Many2one(
        "alfa_core_loaner.allocation", compute="_compute_current_allocation", store=True
    )
    utilization_pct_30d = fields.Float(
        string="Utilization (30d %)", compute="_compute_utilization", store=False
    )

    _plate_uniq = models.Constraint(
        "UNIQUE(license_plate)",
        "License plate must be unique.",
    )

    @api.depends("allocation_ids.state")
    def _compute_current_allocation(self):
        for v in self:
            current = v.allocation_ids.filtered(lambda a: a.state in ("scheduled", "active"))
            v.current_allocation_id = current[:1].id if current else False

    def _compute_utilization(self):
        """Days allocated in the last 30 / 30. Recompute on view, not stored."""
        from datetime import timedelta

        today = fields.Date.context_today(self)
        window_start = today - timedelta(days=30)
        for v in self:
            allocations = v.allocation_ids.filtered(
                lambda a: (
                    a.state in ("active", "completed")
                    and a.actual_return_date
                    and a.actual_return_date >= window_start
                )
            )
            days_used = sum(
                (min(a.actual_return_date, today) - max(a.pickup_date, window_start)).days
                for a in allocations
                if a.pickup_date and a.actual_return_date
            )
            v.utilization_pct_30d = (days_used / 30.0) * 100.0 if days_used else 0.0
