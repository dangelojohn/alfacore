# SPDX-License-Identifier: LGPL-3.0-only
"""Service bay — a physical workstation in the shop.

JTBD §3.2.3 — bay allocation is operational concrete. AlfaCore models it
explicitly rather than using project.task assignment for clarity.
"""

from odoo import api, fields, models


class AlfaServiceBay(models.Model):
    _name = "alfa_service.bay"
    _description = "Service Bay"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    location_id = fields.Many2one(
        "res.partner", string="Location", domain=[("is_company", "=", True)]
    )
    bay_type = fields.Selection(
        [
            ("general", "General Service"),
            ("alignment", "Alignment / Wheel Service"),
            ("diagnostic", "Diagnostic"),
            ("track_prep", "Track Prep"),
            ("body", "Body / Paint"),
        ],
        default="general",
        required=True,
    )
    capacity_vehicles = fields.Integer(default=1, help="Vehicles fitting simultaneously.")
    lift_type = fields.Selection(
        [
            ("two_post", "Two-Post Lift"),
            ("four_post", "Four-Post / Alignment"),
            ("scissor", "Scissor"),
            ("ground", "Ground (no lift)"),
        ]
    )
    current_order_id = fields.Many2one("sale.order", compute="_compute_current_order")
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Bay code must be unique.",
    )

    @api.depends()
    def _compute_current_order(self):
        for bay in self:
            orders = self.env["sale.order"].search(
                [
                    ("alfa_bay_id", "=", bay.id),
                    ("alfa_service_state", "=", "in_progress"),
                ],
                limit=1,
            )
            bay.current_order_id = orders.id if orders else False
