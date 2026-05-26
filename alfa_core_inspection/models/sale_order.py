# SPDX-License-Identifier: LGPL-3.0-only
"""sale.order extension — link to inspections."""

from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    inspection_ids = fields.One2many(
        "alfa_core_inspection.inspection", "sale_order_id", string="Inspections"
    )
    inspection_count = fields.Integer(compute="_compute_inspection_count")

    @api.depends("inspection_ids")
    def _compute_inspection_count(self):
        for so in self:
            so.inspection_count = len(so.inspection_ids)

    def action_view_inspections(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Inspections"),
            "res_model": "alfa_core_inspection.inspection",
            "view_mode": "list,form",
            "domain": [("sale_order_id", "=", self.id)],
            "context": {
                "default_sale_order_id": self.id,
                "default_vehicle_id": self.alfa_vehicle_id.id,
            },
        }
