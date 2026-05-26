# SPDX-License-Identifier: LGPL-3.0-only
"""A single scan run — anchored to a vehicle, originates DTCs and PIDs.

Pattern 4 — per-vehicle isolation. Every session has exactly one vehicle.
Pattern 5 — idempotent: each session is immutable once committed.
"""

from odoo import _, api, fields, models


class AlfaScanSession(models.Model):
    _name = "alfa_core_scanner.scan_session"
    _description = "Scan Session"
    _inherit = ["mail.thread"]
    _order = "started_at desc, id desc"
    _rec_name = "name"

    name = fields.Char(required=True, copy=False, readonly=True, default=lambda s: _("New"))
    vehicle_id = fields.Many2one("alfa_fleet.vehicle", required=True, tracking=True, index=True)
    device_id = fields.Many2one("alfa_core_scanner.device", required=True, tracking=True)
    started_at = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    ended_at = fields.Datetime()
    duration_seconds = fields.Integer(compute="_compute_duration", store=True)
    mileage_at_scan = fields.Integer(string="Mileage at Scan (km)")
    battery_voltage = fields.Float(string="Battery Voltage (V)")

    modules_scanned = fields.Char(
        string="ECUs Scanned", help="Comma-separated module list: ECM, TCM, ABS, AFLS, BCM, etc."
    )
    dtc_ids = fields.One2many("alfa_core_scanner.scan_dtc", "scan_session_id", string="DTCs")
    pid_ids = fields.One2many(
        "alfa_core_scanner.scan_pid", "scan_session_id", string="PID Readings"
    )
    dtc_count = fields.Integer(compute="_compute_dtc_count", store=True)

    state = fields.Selection(
        [
            ("running", "Running"),
            ("complete", "Complete"),
            ("aborted", "Aborted"),
            ("uploaded", "Uploaded to Backend"),
        ],
        default="running",
        required=True,
        tracking=True,
    )
    inference_zde = fields.Boolean(
        string="ZDE",
        default=True,
        help="Inherits from subscription. ZDE=True keeps this session local only.",
    )
    # `diagnosis_report_id` lives in alfa_core_diagnosis as an _inherit
    # extension to avoid a circular dep (scanner -> diagnosis -> scanner).

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "alfa_core_scanner.scan_session"
                ) or _("New")
        return super().create(vals_list)

    @api.depends("started_at", "ended_at")
    def _compute_duration(self):
        for s in self:
            if s.started_at and s.ended_at:
                s.duration_seconds = int((s.ended_at - s.started_at).total_seconds())
            else:
                s.duration_seconds = 0

    @api.depends("dtc_ids")
    def _compute_dtc_count(self):
        for s in self:
            s.dtc_count = len(s.dtc_ids)
