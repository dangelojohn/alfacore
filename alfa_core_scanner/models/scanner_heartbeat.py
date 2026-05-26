# SPDX-License-Identifier: LGPL-3.0-only
"""Scanner heartbeat — offline detection / device health."""

from odoo import fields, models


class AlfaScannerHeartbeat(models.Model):
    _name = "alfa_core_scanner.heartbeat"
    _description = "Scanner Heartbeat"
    _order = "received_at desc"

    device_id = fields.Many2one(
        "alfa_core_scanner.device", required=True, ondelete="cascade", index=True
    )
    received_at = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    rssi = fields.Float(string="RSSI", help="Signal strength when last seen.")
    battery_voltage = fields.Float(string="Vehicle Battery (V)")
    firmware_version = fields.Char()
    notes = fields.Text()
