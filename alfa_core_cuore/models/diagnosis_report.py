# SPDX-License-Identifier: LGPL-3.0-only
"""Diagnosis report extension: the CUORE job on top of an AlfaCore report.

The importer sets the state only to ``draft`` / ``pending_review``; ``reviewed`` and
``delivered`` are an AlfaCore person's decision. ``confidence`` is left at its default:
no number is synthesised from CUORE's likelihood labels.
"""

from odoo import api, fields, models

from .cuore_hypothesis import EVIDENCE_CLASSES, EVIDENCE_RANK
from .guard import guard_write

# Fields on the report that belong to the CUORE ledger. The summary, severity, review
# fields and state stay editable by advisors.
_LOCKED = {
    "cuore_bundle_id",
    "cuore_job_key",
    "cuore_job_id",
    "cuore_station_id",
    "cuore_job_status",
    "cuore_job_outcome",
    "cuore_complaint",
    "cuore_technician",
    "cuore_proof_present",
    "cuore_proof_criteria",
    "cuore_proof_json",
    "hypothesis_ids",
    "scan_session_id",
}


class AlfaDiagnosisReport(models.Model):
    _inherit = "alfa_core_diagnosis.report"

    cuore_bundle_id = fields.Many2one(
        "alfa.cuore.bundle",
        string="CUORE Bundle",
        readonly=True,
        index=True,
        ondelete="set null",
        copy=False,
    )
    cuore_job_key = fields.Char(string="CUORE Job Key", readonly=True, copy=False, index=True)
    cuore_job_id = fields.Char(string="CUORE Job", readonly=True, copy=False)
    cuore_station_id = fields.Char(string="CUORE Station", readonly=True, copy=False)
    cuore_job_status = fields.Char(string="Job Status (CUORE)", readonly=True, copy=False)
    cuore_job_outcome = fields.Char(
        string="Job Outcome (CUORE)",
        readonly=True,
        copy=False,
        help="fixed / not_fixed / deferred, as the mechanic recorded it in CUORE.",
    )
    cuore_complaint = fields.Text(string="Complaint (CUORE)", readonly=True, copy=False)
    cuore_technician = fields.Char(string="Technician (CUORE)", readonly=True, copy=False)
    hypothesis_ids = fields.One2many(
        "alfa.cuore.hypothesis", "report_id", string="CUORE Hypotheses", readonly=True
    )
    cuore_evidence_class = fields.Selection(
        EVIDENCE_CLASSES,
        string="Weakest Evidence Class",
        compute="_compute_cuore_evidence_class",
        help="Weakest class among this job's live hypotheses. Shown beside any "
        "confidence-like value: a conclusion is only as strong as its weakest support.",
    )
    cuore_proof_present = fields.Boolean(string="Proof-of-Fix Recorded", readonly=True, copy=False)
    cuore_proof_criteria = fields.Text(
        string="Proof-of-Fix Criteria",
        readonly=True,
        copy=False,
        help="What would count as proof the repair worked, per code, with its evidence class.",
    )
    cuore_proof_json = fields.Text(
        string="Proof-of-Fix (JSON)",
        readonly=True,
        copy=False,
        help="Criteria, verification, clear evidence and outcome as CUORE exported them.",
    )

    _cuore_job_key_uniq = models.Constraint(
        "UNIQUE(cuore_job_key)", "This CUORE job was already imported (duplicate job key)."
    )

    @api.depends("hypothesis_ids.evidence_class", "hypothesis_ids.deleted")
    def _compute_cuore_evidence_class(self):
        for rec in self:
            live = rec.hypothesis_ids.filtered(lambda h: not h.deleted)
            rec.cuore_evidence_class = (
                min(live.mapped("evidence_class"), key=EVIDENCE_RANK.__getitem__) if live else False
            )

    def write(self, vals):
        guard_write(self.filtered("cuore_bundle_id"), vals, locked_fields=_LOCKED)
        return super().write(vals)
