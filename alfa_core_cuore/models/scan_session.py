# SPDX-License-Identifier: LGPL-3.0-only
"""Scan session extension: provenance, UDS status context and CUORE JSON blobs.

Pattern 10 (honest boundaries): ``cuore_from_car`` is true only when CUORE says the
stream was a real serial link. A replayed or scripted stream is stored but never
shown as a reading.
"""

from odoo import _, api, fields, models

from .guard import MAIL_FIELDS, guard_unlink, guard_write

# Fields the diagnosis module (or a person) may still set on an imported session.
_FREE = MAIL_FIELDS | {"diagnosis_report_id"}


class AlfaScanSession(models.Model):
    _inherit = "alfa_core_scanner.scan_session"

    cuore_bundle_id = fields.Many2one(
        "alfa.cuore.bundle",
        string="CUORE Bundle",
        readonly=True,
        index=True,
        ondelete="set null",
        copy=False,
        help="Provenance of every imported row.",
    )
    cuore_source = fields.Char(
        string="Source",
        readonly=True,
        copy=False,
        help='Set to "CUORE wired adapter" on sessions created by the CUORE importer.',
    )
    cuore_external_key = fields.Char(
        string="CUORE Key",
        readonly=True,
        copy=False,
        index=True,
        help="station_id:scan_id (scan) or job:station_id:job_id (job anchor). Unique.",
    )
    cuore_session_role = fields.Selection(
        [("scan", "CUORE scan"), ("job_anchor", "Job anchor (no readings)")],
        string="CUORE Role",
        readonly=True,
        copy=False,
        help="A job bundle carries no scan; its report needs a session, so an empty anchor "
        "session holds the link. It contains no readings.",
    )
    cuore_scan_status = fields.Selection(
        [("complete", "Complete"), ("partial", "Partial"), ("attempt", "Attempt")],
        string="CUORE Scan Status",
        readonly=True,
        copy=False,
        help="Only 'complete' counts as a completed scan. Partial and attempt scans do not.",
    )
    cuore_from_car = fields.Boolean(
        string="From Car",
        readonly=True,
        copy=False,
        help="True only if CUORE read this over a real serial link to the car.",
    )
    cuore_stream = fields.Char(string="Stream", readonly=True, copy=False)
    cuore_cable = fields.Char(string="Cable", readonly=True, copy=False)
    cuore_buses_attempted = fields.Char(string="Buses Attempted", readonly=True, copy=False)
    cuore_finalized = fields.Boolean(string="Finalized", readonly=True, copy=False)
    cuore_count_active = fields.Integer(string="Active Codes", readonly=True, copy=False)
    cuore_count_history = fields.Integer(string="History Codes", readonly=True, copy=False)
    cuore_count_not_run = fields.Integer(
        string="Tracked, Not Faults",
        readonly=True,
        copy=False,
        help="Codes a module tracks but that are neither active nor history. Not faults.",
    )
    cuore_freeze_frame_json = fields.Text(
        string="Freeze Frames (JSON)",
        readonly=True,
        copy=False,
        help="Mode 02 freeze frames and UDS 19 04 / 19 06 snapshots, as recorded.",
    )
    cuore_mode06_json = fields.Text(
        string="Mode 06 (JSON)",
        readonly=True,
        copy=False,
        help="On-board test results. AlfaCore has no Mode 06 model; kept as recorded.",
    )
    cuore_coverage_json = fields.Text(
        string="Coverage (JSON)",
        readonly=True,
        copy=False,
        help="Which modules answered, stayed silent or were not reachable. "
        "A silent module is 'no answer', never 'no codes'.",
    )
    cuore_readiness_json = fields.Text(string="Readiness (JSON)", readonly=True, copy=False)
    cuore_requirements_json = fields.Text(
        string="Scan Requirements (JSON)", readonly=True, copy=False
    )
    cuore_scan_meta_json = fields.Text(
        string="Scan Header (JSON)",
        readonly=True,
        copy=False,
        help="Guided-scan segments, steps, counts and the EVAP bundle.",
    )

    _cuore_external_key_uniq = models.Constraint(
        "UNIQUE(cuore_external_key)",
        "This CUORE scan was already imported (duplicate external key).",
    )

    def write(self, vals):
        guard_write(self.filtered("cuore_bundle_id"), vals, free_fields=_FREE)
        return super().write(vals)

    def unlink(self):
        guard_unlink(self.filtered("cuore_bundle_id"))
        return super().unlink()

    @api.depends("cuore_source", "cuore_from_car")
    def _compute_cuore_reading_label(self):
        for rec in self:
            rec.cuore_reading_label = (
                _("Reading from the car")
                if rec.cuore_from_car
                else _("NOT a reading from the car")
                if rec.cuore_source
                else False
            )

    cuore_reading_label = fields.Char(compute="_compute_cuore_reading_label")
