# SPDX-License-Identifier: LGPL-3.0-only
"""CUORE hypotheses and their evidence references, read-only in AlfaCore.

Decision D1 (integration spec): CUORE owns hypothesis status. AlfaCore shows each
hypothesis with its status, likelihood label and evidence class, and rejects edits.

Pattern 10 (honest boundaries): a hypothesis is an inference at best, never a reading.
No numeric confidence is invented from the likelihood label.
"""

from odoo import api, fields, models

from .guard import MAIL_FIELDS, guard_unlink, guard_write

EVIDENCE_CLASSES = [
    ("reading", "Reading (this car, real serial link)"),
    ("inference", "Inference"),
    ("owner_attested", "Owner / person attested"),
    ("outside_literature", "Outside literature (not this car)"),
]
EVIDENCE_RANK = {"reading": 3, "inference": 2, "owner_attested": 1, "outside_literature": 0}


class AlfaCuoreHypothesis(models.Model):
    _name = "alfa.cuore.hypothesis"
    _description = "CUORE Hypothesis"
    _order = "report_id, deleted, id"
    _rec_name = "text"

    report_id = fields.Many2one(
        "alfa_core_diagnosis.report", required=True, ondelete="cascade", index=True
    )
    bundle_id = fields.Many2one("alfa.cuore.bundle", ondelete="set null", index=True)
    vehicle_id = fields.Many2one(related="report_id.vehicle_id", store=True, index=True)
    hyp_id = fields.Char(string="CUORE Hypothesis ID", required=True, readonly=True)
    external_key = fields.Char(
        readonly=True, copy=False, help="station_id:job_id:hyp_id. Unique per hypothesis."
    )
    text = fields.Text(string="Hypothesis", required=True)
    system = fields.Char()
    status = fields.Selection(
        [
            ("open", "Open"),
            ("supported", "Supported"),
            ("confirmed", "Confirmed"),
            ("refuted", "Refuted"),
        ],
        required=True,
        help="CUORE's status, read-only here. Confirmed and refuted come from CUORE only.",
    )
    likelihood = fields.Char(
        string="Likelihood Label",
        help="low / med / high as CUORE labels it. Never converted to a number.",
    )
    next_test = fields.Text()
    codes = fields.Char(string="DTCs")
    safety = fields.Boolean(string="Safety Hypothesis")
    attested_resolved = fields.Boolean(string="Attested Resolved")
    deleted = fields.Boolean(
        string="Deleted in CUORE", help="Soft-deleted hypotheses stay for the audit trail."
    )
    evidence_class = fields.Selection(
        EVIDENCE_CLASSES,
        required=True,
        help="Weakest class among the hypothesis text and its supports, as sent by CUORE.",
    )
    evidence_class_basis = fields.Char()
    audit_json = fields.Text(string="CUORE Audit Trail (JSON)")
    evidence_ids = fields.One2many("alfa.cuore.evidence", "hypothesis_id", string="Evidence")
    evidence_count = fields.Integer(compute="_compute_evidence_count")

    _external_key_uniq = models.Constraint(
        "UNIQUE(external_key)", "This CUORE hypothesis was already imported."
    )

    @api.depends("evidence_ids")
    def _compute_evidence_count(self):
        for rec in self:
            rec.evidence_count = len(rec.evidence_ids)

    def write(self, vals):
        guard_write(self, vals, free_fields=MAIL_FIELDS)
        return super().write(vals)

    def unlink(self):
        guard_unlink(self)
        return super().unlink()


class AlfaCuoreEvidence(models.Model):
    _name = "alfa.cuore.evidence"
    _description = "CUORE Evidence Reference"
    _order = "hypothesis_id, side, id"

    hypothesis_id = fields.Many2one(
        "alfa.cuore.hypothesis", required=True, ondelete="cascade", index=True
    )
    side = fields.Selection([("for", "For"), ("against", "Against")], required=True)
    kind = fields.Char(
        help="code, freeze_frame, actuator, live, inspection, symptom, note, test, ..."
    )
    ref_id = fields.Char(string="CUORE Reference")
    label = fields.Char()
    result = fields.Char(help="pass / fail / inconclusive / not_possible, as recorded.")
    evidence_class = fields.Selection(EVIDENCE_CLASSES, required=True)

    def write(self, vals):
        guard_write(self, vals, free_fields=MAIL_FIELDS)
        return super().write(vals)

    def unlink(self):
        guard_unlink(self)
        return super().unlink()
