# SPDX-License-Identifier: LGPL-3.0-only
"""A single PID reading captured during a scan."""

from odoo import fields, models


class AlfaScanPID(models.Model):
    _name = "alfa_core_scanner.scan_pid"
    _description = "Scan PID Reading"
    _order = "scan_session_id, pid_id"

    scan_session_id = fields.Many2one(
        "alfa_core_scanner.scan_session", required=True, ondelete="cascade", index=True
    )
    pid_id = fields.Char(
        string="PID",
        required=True,
        help="OBD-II PID identifier, e.g. '010C' (RPM), '0105' (Coolant temp).",
    )
    pid_name = fields.Char(string="PID Name")
    value = fields.Float()
    units = fields.Char(string="Units")
    raw_payload = fields.Text(string="Raw OBD Payload")
