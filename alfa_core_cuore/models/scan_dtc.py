# SPDX-License-Identifier: LGPL-3.0-only
"""Scan DTC extension: UDS status byte, decoded flags, bus and source service.

MODEL_MAP 15.3: ``dtc_status`` has four labels only; the raw status byte and its eight
named bits had no home. A code that a module merely tracks is not a fault and gets no
row here (it is counted on the session).
"""

from odoo import fields, models

from .guard import MAIL_FIELDS, guard_unlink, guard_write


class AlfaScanDTC(models.Model):
    _inherit = "alfa_core_scanner.scan_dtc"

    cuore_imported = fields.Boolean(string="From CUORE", readonly=True, copy=False, index=True)
    cuore_from_car = fields.Boolean(
        string="From Car",
        readonly=True,
        copy=False,
        help="False for a replayed or scripted stream: stored, never shown as a reading.",
    )
    status_byte = fields.Integer(
        string="UDS Status Byte",
        readonly=True,
        copy=False,
        help="Raw ISO 14229 DTC status byte, always kept as read.",
    )
    status_flags_json = fields.Text(
        string="Decoded Status Flags (JSON)",
        readonly=True,
        copy=False,
        help="The eight named status bits, as CUORE decoded them.",
    )
    failure_type_byte = fields.Char(string="Failure Type Byte", readonly=True, copy=False)
    bus = fields.Char(string="Bus", readonly=True, copy=False)
    source_service = fields.Selection(
        [
            ("uds_19_02", "UDS 19 02"),
            ("obd_03", "OBD Mode 03 (stored)"),
            ("obd_07", "OBD Mode 07 (pending)"),
            ("obd_0a", "OBD Mode 0A (permanent)"),
        ],
        readonly=True,
        copy=False,
    )

    def write(self, vals):
        guard_write(self.filtered("cuore_imported"), vals, free_fields=MAIL_FIELDS)
        return super().write(vals)

    def unlink(self):
        guard_unlink(self.filtered("cuore_imported"))
        return super().unlink()
