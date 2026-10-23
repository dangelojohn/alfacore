# SPDX-License-Identifier: LGPL-3.0-only
"""Import wizard: upload a .cuore.zip -> validate -> preview -> import.

Nothing is written before the person presses Import (integration spec 6.3). The wizard
holds no import logic of its own: it calls ``alfa.cuore.bundle`` (``inspect_bundle`` and
``_import``), the single service method that a later REST route could also call.
"""

import base64

from odoo import _, fields, models
from odoo.exceptions import UserError


class AlfaCuoreImportWizard(models.TransientModel):
    _name = "alfa.cuore.import.wizard"
    _description = "Import CUORE Bundle"

    state = fields.Selection(
        [
            ("upload", "Upload"),
            ("invalid", "Rejected"),
            ("preview", "Preview"),
            ("already", "Already imported"),
            ("done", "Imported"),
        ],
        default="upload",
        required=True,
    )
    file = fields.Binary(string="Bundle (.cuore.zip)", attachment=False)
    filename = fields.Char()
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Service Order",
        domain=[("alfa_vehicle_id", "!=", False)],
        help="Optional. If set, the bundle's VIN must equal the order's vehicle VIN.",
    )

    # Validation + preview
    report = fields.Text(string="Validation Report", readonly=True)
    bundle_uuid = fields.Char(string="Bundle UUID", readonly=True)
    kind = fields.Selection([("scan", "Scan"), ("job", "Job")], readonly=True)
    station_id = fields.Char(string="Station", readonly=True)
    vin = fields.Char(string="VIN", readonly=True)
    vehicle_id = fields.Many2one("alfa_fleet.vehicle", string="Matched Vehicle", readonly=True)
    created_at = fields.Datetime(string="Created (UTC)", readonly=True)
    age_days = fields.Integer(string="Age (days)", readonly=True)
    finalized = fields.Boolean(readonly=True)
    n_dtc_active = fields.Integer(string="Active DTCs", readonly=True)
    n_dtc_history = fields.Integer(string="History DTCs", readonly=True)
    n_dtc_not_run = fields.Integer(string="Tracked, not faults", readonly=True)
    n_hypotheses = fields.Integer(string="Hypotheses", readonly=True)
    n_hypotheses_deleted = fields.Integer(string="Deleted hypotheses", readonly=True)
    n_steps = fields.Integer(string="Mechanic steps", readonly=True)
    class_summary = fields.Char(string="Hypotheses by evidence class", readonly=True)
    existing_bundle_id = fields.Many2one("alfa.cuore.bundle", readonly=True)
    result_bundle_id = fields.Many2one("alfa.cuore.bundle", readonly=True)

    # ------------------------------------------------------------------------
    def _data(self):
        self.ensure_one()
        if not self.file:
            raise UserError(_("Choose a .cuore.zip file first."))
        return base64.b64decode(self.file)

    def _reopen(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "name": _("Import CUORE bundle"),
        }

    def _show(self, res):
        """Copy an ``inspect_bundle`` result onto the wizard."""
        manifest, summary = res["manifest"], res["summary"]
        bundle = self.env["alfa.cuore.bundle"]
        header = bundle._safe_header(manifest)
        age = (fields.Datetime.now() - header["created_at"]).days if header["created_at"] else 0
        by_class = summary.get("by_class") or {}
        self.write(
            {
                "report": bundle._report_text(res["errors"], res["warnings"]),
                "bundle_uuid": str(manifest.get("bundle_uuid") or "")[:64] or False,
                "kind": header["kind"],
                "station_id": header["station_id"],
                "vin": header["vin"],
                "vehicle_id": res["vehicle"].id or False,
                "created_at": header["created_at"],
                "age_days": age,
                "finalized": header["finalized"],
                "n_dtc_active": summary.get("dtc_active", 0),
                "n_dtc_history": summary.get("dtc_history", 0),
                "n_dtc_not_run": summary.get("dtc_not_run", 0),
                "n_hypotheses": summary.get("hypotheses", 0),
                "n_hypotheses_deleted": summary.get("hypotheses_deleted", 0),
                "n_steps": summary.get("steps", 0),
                "class_summary": ", ".join(f"{k}: {v}" for k, v in by_class.items() if v) or False,
                "existing_bundle_id": res["existing"].id or False,
            }
        )

    # ------------------------------------------------------------------------
    def action_validate(self):
        """Step 2 and 3: validate, then preview. Writes nothing but the wizard itself."""
        self.ensure_one()
        res = self.env["alfa.cuore.bundle"].inspect_bundle(self._data(), self.sale_order_id)
        self._show(res)
        if res["errors"]:
            self.state = "invalid"
        elif res["already"]:
            self.state = "already"
        else:
            self.state = "preview"
        return self._reopen()

    def action_import(self):
        """Step 4 and 5: import in one transaction, attributed to the current user."""
        self.ensure_one()
        out = self.env["alfa.cuore.bundle"]._import(
            self._data(), self.filename or "", self.sale_order_id
        )
        bundle = out["bundle"]
        if out["outcome"] == "already":
            self.write({"state": "already", "existing_bundle_id": bundle.id})
        elif out["outcome"] == "imported":
            self.write(
                {
                    "state": "done",
                    "result_bundle_id": bundle.id,
                    "report": self.env["alfa.cuore.bundle"]._report_text([], out["warnings"]),
                }
            )
        else:
            self.write(
                {
                    "state": "invalid",
                    "report": self.env["alfa.cuore.bundle"]._report_text(
                        out["errors"], out["warnings"]
                    ),
                }
            )
        return self._reopen()

    def action_back(self):
        self.ensure_one()
        self.write({"state": "upload", "file": False, "filename": False, "report": False})
        return self._reopen()

    def action_open_bundle(self):
        self.ensure_one()
        bundle = self.result_bundle_id or self.existing_bundle_id
        if not bundle:
            raise UserError(_("There is no bundle record to open."))
        return {
            "type": "ir.actions.act_window",
            "res_model": bundle._name,
            "res_id": bundle.id,
            "view_mode": "form",
        }
