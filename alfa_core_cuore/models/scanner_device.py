# SPDX-License-Identifier: LGPL-3.0-only
"""Scanner device extension: the wired bay adapter behind a CUORE station.

MODEL_MAP 6: the device model is BLE-shaped (pairing, RSSI). A wired adapter has no
pairing step, so the connector never requires ``partner_id`` / ``vehicle_id`` on it.
"""

from odoo import fields, models


class AlfaScannerDevice(models.Model):
    _inherit = "alfa_core_scanner.device"

    model_name = fields.Selection(
        selection_add=[("cuore_stn", "CUORE wired bay adapter")],
        ondelete={"cuore_stn": "set default"},
    )
    cuore_station_id = fields.Char(
        string="CUORE Station",
        index=True,
        readonly=True,
        help="Station slug from the bundle manifest. One device per station adapter.",
    )
    cuore_transport = fields.Selection(
        [("serial_usb", "Serial / USB (wired)")],
        string="Transport",
        readonly=True,
        help="Wired adapters have no Bluetooth pairing and report no signal strength.",
    )
