# SPDX-License-Identifier: LGPL-3.0-only
"""Inspection extension: CUORE mechanic steps as internal inspection lines.

The connector never calls ``action_send_to_customer``, so these inspections stay
internal and never reach the portal. Steps are diagnostic, not sales lines:
``remediation_recommended`` stays empty so ``action_apply_to_so`` creates nothing.
"""

from odoo import fields, models

from .cuore_hypothesis import EVIDENCE_CLASSES
from .guard import guard_unlink, guard_write

_INSPECTION_LOCKED = {"cuore_bundle_id", "cuore_hyp_key", "vehicle_id", "template_id"}
_STEP_LOCKED = {
    "step_key",
    "step_order",
    "step_kind",
    "step_source",
    "step_tools",
    "step_bulletins",
    "step_done",
    "step_done_ref",
    "evidence_class",
    "name",
    "note",
}


class AlfaInspection(models.Model):
    _inherit = "alfa_core_inspection.inspection"

    cuore_bundle_id = fields.Many2one(
        "alfa.cuore.bundle",
        string="CUORE Bundle",
        readonly=True,
        index=True,
        ondelete="set null",
        copy=False,
    )
    cuore_hyp_key = fields.Char(
        string="CUORE Plan Key",
        readonly=True,
        copy=False,
        index=True,
        help="station_id:job_id:hyp_id of the hypothesis this plan belongs to.",
    )

    def write(self, vals):
        guard_write(self.filtered("cuore_bundle_id"), vals, locked_fields=_INSPECTION_LOCKED)
        return super().write(vals)

    def unlink(self):
        guard_unlink(self.filtered("cuore_bundle_id"))
        return super().unlink()


class AlfaInspectionFinding(models.Model):
    _inherit = "alfa_core_inspection.finding"

    step_key = fields.Char(
        string="Step Key",
        readonly=True,
        copy=False,
        index=True,
        help="Stable identity of a CUORE plan step. The order number is not identity: it "
        "renumbers when a step becomes done.",
    )
    step_order = fields.Integer(string="CUORE Step No.", readonly=True, copy=False)
    step_kind = fields.Char(
        string="Step Kind",
        readonly=True,
        copy=False,
        help="precondition, vin_check, read, flash, test, drive_cycle, decide, inspect, record.",
    )
    step_source = fields.Text(
        string="Step Source",
        readonly=True,
        copy=False,
        help="Keeps the OUTSIDE LITERATURE prefix where CUORE set it.",
    )
    step_tools = fields.Char(string="Tools", readonly=True, copy=False)
    step_bulletins = fields.Char(string="Bulletins", readonly=True, copy=False)
    step_done = fields.Boolean(string="Done in CUORE", readonly=True, copy=False)
    step_done_ref = fields.Char(string="Done Reference", readonly=True, copy=False)
    evidence_class = fields.Selection(
        EVIDENCE_CLASSES, string="Evidence Class", readonly=True, copy=False
    )

    _step_key_uniq = models.Constraint(
        "UNIQUE(inspection_id, step_key)", "Duplicate CUORE step in one inspection."
    )

    def write(self, vals):
        guard_write(self.filtered("step_key"), vals, locked_fields=_STEP_LOCKED)
        return super().write(vals)
