# SPDX-License-Identifier: LGPL-3.0-only
"""Parts vendor — Alfa Romeo dealers, aftermarket houses, direct."""

from odoo import fields, models


class AlfaPartsVendor(models.Model):
    _name = "alfa_parts.part.vendor"
    _description = "Parts Vendor"
    _order = "sequence, name"

    name = fields.Char(required=True)
    vendor_type = fields.Selection(
        [
            ("oem_dealer", "OEM Dealer"),
            ("aftermarket", "Aftermarket House"),
            ("mopar_direct", "MOPAR Direct"),
            ("specialty", "Specialty / Performance"),
        ],
        default="aftermarket",
        required=True,
    )
    partner_id = fields.Many2one(
        "res.partner", string="Vendor Account", help="Links to the procurement-side partner record."
    )
    contact_phone = fields.Char()
    contact_email = fields.Char()
    website = fields.Char()
    delivery_days_typical = fields.Float(string="Typical Delivery (days)")
    notes = fields.Text()
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
