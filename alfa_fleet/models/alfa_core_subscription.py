# SPDX-License-Identifier: LGPL-3.0-only
"""Extend alfa_core.subscription to add vehicle_ids — closes Sprint 1 TODO."""

from odoo import api, fields, models


class AlfaCoreSubscription(models.Model):
    _inherit = "alfa_core.subscription"

    vehicle_ids = fields.Many2many(
        comodel_name="alfa_fleet.vehicle",
        relation="alfa_core_subscription_vehicle_rel",
        column1="subscription_id",
        column2="vehicle_id",
        string="Covered Vehicles",
        help="Vehicles covered by this subscription. Multi-vehicle households "
        "on Premium/Pro tiers attach more than one.",
    )
    vehicle_count = fields.Integer(compute="_compute_vehicle_count")

    @api.depends("vehicle_ids")
    def _compute_vehicle_count(self):
        for sub in self:
            sub.vehicle_count = len(sub.vehicle_ids)
