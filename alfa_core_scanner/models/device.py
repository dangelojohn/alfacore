# SPDX-License-Identifier: LGPL-3.0-only
"""Paired OBD-II BLE scanner (Vgate iCar Pro, OBDLink MX+).

Per Service Plan §6.1 — the scanner is the moat. Customer-owned hardware
that ships with onboarding. Bluetooth pairing happens in the PWA.
"""

from odoo import api, fields, models


class AlfaScannerDevice(models.Model):
    _name = "alfa_core_scanner.device"
    _description = "OBD-II Scanner Device"
    _inherit = ["mail.thread"]
    _order = "create_date desc"
    _rec_name = "display_name"

    serial_number = fields.Char(string="Serial Number", required=True, copy=False, tracking=True)
    display_name = fields.Char(compute="_compute_display_name", store=True)
    model_name = fields.Selection(
        [
            ("vgate_icar_pro", "Vgate iCar Pro BLE 4.0"),
            ("obdlink_mx_plus", "OBDLink MX+"),
            ("other", "Other"),
        ],
        string="Model",
        required=True,
        default="vgate_icar_pro",
    )
    firmware_version = fields.Char(tracking=True)
    partner_id = fields.Many2one("res.partner", string="Owner", tracking=True, index=True)
    vehicle_id = fields.Many2one(
        "alfa_fleet.vehicle",
        string="Paired Vehicle",
        tracking=True,
        index=True,
        help="Vehicle this scanner is currently paired with. Null when in transit.",
    )
    paired_date = fields.Datetime()
    last_seen = fields.Datetime(string="Last Heartbeat", readonly=True)
    state = fields.Selection(
        [
            ("shipped", "Shipped"),
            ("paired", "Paired"),
            ("active", "Active"),
            ("offline", "Offline"),
            ("returned", "Returned"),
            ("decommissioned", "Decommissioned"),
        ],
        default="shipped",
        required=True,
        tracking=True,
    )

    _serial_uniq = models.Constraint(
        "UNIQUE(serial_number)",
        "Serial number must be unique.",
    )

    @api.depends("serial_number", "model_name", "partner_id")
    def _compute_display_name(self):
        for d in self:
            d.display_name = f"{d.serial_number} ({d.model_name or ''})"
