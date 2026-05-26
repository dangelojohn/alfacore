# SPDX-License-Identifier: LGPL-3.0-only
"""DTC library — P-codes, B-codes, C-codes, U-codes.

Seeded from SAE J2012 and OEM-specific Stellantis codes.
Loaded via data XML; admin-editable for OEM customization.
"""

from odoo import fields, models


class AlfaDiagnosisDTC(models.Model):
    _name = "alfa_core_diagnosis.dtc"
    _description = "DTC Library Entry"
    _order = "code"
    _rec_name = "code"

    code = fields.Char(required=True, index=True, help="DTC code, e.g. 'P0301'.")
    name = fields.Char(string="Description", required=True, translate=True)
    description_long = fields.Text(
        translate=True, help="Customer-facing plain-English explanation."
    )
    category = fields.Selection(
        [
            ("powertrain", "Powertrain (P)"),
            ("body", "Body (B)"),
            ("chassis", "Chassis (C)"),
            ("network", "Network (U)"),
        ],
        required=True,
    )
    severity = fields.Selection(
        [
            ("info", "Informational"),
            ("warn", "Warning"),
            ("severe", "Severe"),
            ("safety_critical", "Safety-Critical"),
        ],
        default="warn",
        required=True,
        # `tracking=True` removed: Odoo 19 doesn't accept it on this model.
        # dtc isn't chatter-enabled (no _inherit = ["mail.thread"] on this
        # model), so tracking was a no-op + a deprecation warning. The audit
        # trail for severity changes lives on diagnosis.report (which does
        # inherit mail.thread) — every report records the severity at the
        # moment it was generated.
        help="Pattern 10 — honest boundary. Safety-critical codes block "
        "save-for-later in the customer PWA.",
    )
    typical_causes = fields.Text(translate=True)
    fits_platform_ids = fields.Many2many(
        "alfa_fleet.platform",
        relation="alfa_diagnosis_dtc_platform_rel",
        string="Applies to Platforms",
    )
    is_safety_critical = fields.Boolean(compute="_compute_safety_critical", store=True)
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint(
        "UNIQUE(code)",
        "DTC code must be unique.",
    )

    def _compute_safety_critical(self):
        for d in self:
            d.is_safety_critical = d.severity == "safety_critical"
