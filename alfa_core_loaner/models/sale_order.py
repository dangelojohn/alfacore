# SPDX-License-Identifier: LGPL-3.0-only
"""sale.order extension — link to loaner allocations."""

from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    loaner_allocation_ids = fields.One2many(
        "alfa_core_loaner.allocation", "sale_order_id", string="Loaner Allocations"
    )
    has_loaner = fields.Boolean(compute="_compute_has_loaner", store=True)

    @api.depends("loaner_allocation_ids.state")
    def _compute_has_loaner(self):
        for so in self:
            so.has_loaner = bool(
                so.loaner_allocation_ids.filtered(lambda a: a.state in ("scheduled", "active"))
            )

    def action_view_loaners(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Loaner Allocations"),
            "res_model": "alfa_core_loaner.allocation",
            "view_mode": "list,form",
            "domain": [("sale_order_id", "=", self.id)],
            "context": {
                "default_sale_order_id": self.id,
                "default_partner_id": self.partner_id.id,
                "default_customer_vehicle_id": self.alfa_vehicle_id.id,
            },
        }
