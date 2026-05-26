# SPDX-License-Identifier: LGPL-3.0-only
"""scan_session extension — adds the back-reference to the diagnosis report.

Lives here (not in alfa_core_scanner) to avoid a circular dependency:
scanner is upstream, diagnosis depends on scanner. Putting the Many2one
to alfa_core_diagnosis.report inside the scanner module would force
scanner to depend on diagnosis, which would be a cycle.
"""

from odoo import fields, models


class AlfaScanSession(models.Model):
    _inherit = "alfa_core_scanner.scan_session"

    diagnosis_report_id = fields.Many2one(
        "alfa_core_diagnosis.report",
        string="Resulting Diagnosis",
        readonly=True,
    )
