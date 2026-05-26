# SPDX-License-Identifier: LGPL-3.0-only
"""Part master with canonical part-number normalization (Pattern 7)."""

import re

from odoo import api, fields, models


def canonicalize_part_number(value):
    """canon_label 7-pass normalization (Pattern 7).

    68377611AA / 68377611-AA / 68377-611AA / 68377611_AA → 68377611AA

    Passes:
    1. Strip whitespace
    2. Uppercase
    3. Remove dashes, underscores, dots
    4. Remove leading zeros from leading numeric groups (preserve internal)
    5. Strip surrounding quotes
    6. Normalize unicode (NFC)
    7. Strip non-alphanumeric except OEM-specific separators

    For now: minimal viable normalization. Expand per real OEM patterns.
    """
    if not value:
        return value
    import unicodedata

    s = unicodedata.normalize("NFC", value)
    s = s.strip().strip("'\"")
    s = s.upper()
    s = re.sub(r"[\s\-_\.]", "", s)
    return s


class AlfaPartsPart(models.Model):
    _name = "alfa_parts.part"
    _description = "AlfaCore Part"
    _inherit = ["mail.thread"]
    _order = "name"
    _rec_name = "display_name"

    part_number = fields.Char(
        string="Part Number",
        required=True,
        tracking=True,
        help="OEM part number as printed/labeled.",
    )
    canon_part_number = fields.Char(
        string="Canonical Part Number",
        compute="_compute_canon",
        store=True,
        index=True,
        help="Pattern 7 normalized form. Used for dedup and lookup.",
    )
    name = fields.Char(string="Description", required=True, translate=True, tracking=True)
    display_name = fields.Char(compute="_compute_display_name", store=True)

    manufacturer = fields.Char(string="Manufacturer", default="MOPAR")
    category = fields.Selection(
        [
            ("engine", "Engine"),
            ("brake", "Brake"),
            ("suspension", "Suspension"),
            ("electrical", "Electrical"),
            ("body", "Body"),
            ("interior", "Interior"),
            ("fluid", "Fluid"),
            ("filter", "Filter"),
            ("tire", "Tire"),
            ("other", "Other"),
        ],
        default="other",
        required=True,
        tracking=True,
    )

    product_id = fields.Many2one(
        "product.product",
        string="Linked Product",
        help="Inventory and pricing handled by the linked product record.",
    )

    fits_platform_ids = fields.Many2many(
        "alfa_fleet.platform", relation="alfa_parts_part_platform_rel", string="Fits Platforms"
    )
    fits_engine_ids = fields.Many2many(
        "alfa_fleet.engine", relation="alfa_parts_part_engine_rel", string="Fits Engines"
    )

    alternative_ids = fields.One2many(
        "alfa_parts.part.alternative", "oem_part_id", string="Aftermarket Alternatives"
    )
    vendor_ids = fields.Many2many(
        "alfa_parts.part.vendor", relation="alfa_parts_part_vendor_rel", string="Vendors"
    )
    active = fields.Boolean(default=True)

    _canon_uniq = models.Constraint(
        "UNIQUE(canon_part_number)",
        "A part with this canonical part number already exists.",
    )

    @api.depends("part_number")
    def _compute_canon(self):
        for part in self:
            part.canon_part_number = canonicalize_part_number(part.part_number)

    @api.depends("part_number", "name")
    def _compute_display_name(self):
        for part in self:
            part.display_name = (
                f"[{part.part_number}] {part.name}" if part.part_number else (part.name or "")
            )

    @api.model
    def find_by_part_number(self, value):
        """Lookup by any spelling of a part number. Returns single recordset."""
        canon = canonicalize_part_number(value)
        return self.search([("canon_part_number", "=", canon)], limit=1)
