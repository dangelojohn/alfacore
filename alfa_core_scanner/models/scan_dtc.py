# SPDX-License-Identifier: LGPL-3.0-only
"""A single DTC captured during a scan."""

from odoo import fields, models


class AlfaScanDTC(models.Model):
    _name = "alfa_core_scanner.scan_dtc"
    _description = "Scan DTC"
    _order = "scan_session_id, sequence, id"

    scan_session_id = fields.Many2one(
        "alfa_core_scanner.scan_session", required=True, ondelete="cascade", index=True
    )
    dtc_code = fields.Char(
        string="DTC Code", required=True, index=True, help="e.g. P0301, P0507, C0561."
    )
    dtc_status = fields.Selection(
        [
            ("active", "Active / Current"),
            ("pending", "Pending"),
            ("history", "History"),
            ("permanent", "Permanent"),
        ],
        default="active",
        required=True,
    )
    module_source = fields.Char(string="Source ECU", help="ECM, TCM, ABS, AFLS, BCM, etc.")
    freeze_frame_data = fields.Text(string="Freeze Frame")
    raw_payload = fields.Text(
        string="Raw OBD Payload", help="Hex bytes as received from the scanner."
    )
    sequence = fields.Integer(default=10)
