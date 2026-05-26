# SPDX-License-Identifier: LGPL-3.0-only
"""Customer vehicle — VIN-keyed master record.

Blueprint §4.2 — central nexus that scanner sessions, service orders,
inspections, and configurator sessions all anchor to.
"""

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")  # ISO 3779 — no I, O, Q


class AlfaFleetVehicle(models.Model):
    _name = "alfa_fleet.vehicle"
    _description = "Customer Vehicle"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"
    _rec_name = "display_name"

    # ------------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------------
    vin = fields.Char(
        string="VIN",
        required=True,
        size=17,
        copy=False,
        tracking=True,
        index=True,
        help="17-character VIN per ISO 3779.",
    )
    display_name = fields.Char(compute="_compute_display_name", store=True)
    license_plate = fields.Char(string="License Plate", tracking=True)
    year = fields.Integer(string="Model Year", required=True, tracking=True)
    color = fields.Char(string="Exterior Color")
    color_interior = fields.Char(string="Interior Color")

    # ------------------------------------------------------------------------
    # Classification (Pattern 4: per-vehicle isolation via VIN)
    # ------------------------------------------------------------------------
    make = fields.Char(string="Make", default="Alfa Romeo", required=True)
    model = fields.Char(
        string="Model",
        required=True,
        tracking=True,
        help="e.g. 'Stelvio', 'Giulia', '4C', 'Tonale'.",
    )
    platform_id = fields.Many2one("alfa_fleet.platform", string="Platform", tracking=True)
    engine_id = fields.Many2one("alfa_fleet.engine", string="Engine", tracking=True)
    trim_id = fields.Many2one("alfa_fleet.trim", string="Trim", tracking=True)

    # ------------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------------
    last_mileage_km = fields.Integer(string="Last Logged Mileage (km)", tracking=True)
    last_mileage_date = fields.Datetime(string="Last Mileage Reading")
    state = fields.Selection(
        [
            ("active", "Active"),
            ("in_service", "In Service"),
            ("sold", "Sold"),
            ("totalled", "Totalled / Out of Service"),
        ],
        default="active",
        required=True,
        tracking=True,
    )

    # ------------------------------------------------------------------------
    # Ownership (M2M through alfa_fleet.vehicle.ownership)
    # ------------------------------------------------------------------------
    ownership_ids = fields.One2many(
        "alfa_fleet.vehicle.ownership",
        "vehicle_id",
        string="Ownership History",
    )
    primary_owner_id = fields.Many2one(
        "res.partner",
        compute="_compute_primary_owner",
        store=True,
        string="Primary Owner",
        help="Current primary_owner from ownership_ids, or null if no active ownership.",
    )

    # ------------------------------------------------------------------------
    # Preferences
    # ------------------------------------------------------------------------
    preference_ids = fields.One2many(
        "alfa_fleet.vehicle.preference",
        "vehicle_id",
        string="Preferences",
    )

    # ------------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------------
    _vin_uniq = models.Constraint(
        "UNIQUE(vin)",
        "VIN must be unique.",
    )

    @api.constrains("vin")
    def _check_vin_format(self):
        for veh in self:
            if veh.vin and not VIN_PATTERN.match(veh.vin.upper()):
                raise ValidationError(
                    _("VIN must be 17 alphanumeric characters (no I, O, Q): %s") % veh.vin
                )

    @api.constrains("year")
    def _check_year(self):
        for veh in self:
            if veh.year and (veh.year < 1980 or veh.year > 2100):
                raise ValidationError(_("Year must be between 1980 and 2100."))

    @api.constrains("last_mileage_km")
    def _check_mileage_positive(self):
        for veh in self:
            if veh.last_mileage_km and veh.last_mileage_km < 0:
                raise ValidationError(_("Mileage cannot be negative."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("vin"):
                vals["vin"] = vals["vin"].upper().strip()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("vin"):
            vals["vin"] = vals["vin"].upper().strip()
        if "last_mileage_km" in vals:
            vals.setdefault("last_mileage_date", fields.Datetime.now())
        return super().write(vals)

    # ------------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------------
    @api.depends("year", "model", "trim_id", "vin")
    def _compute_display_name(self):
        for veh in self:
            parts = []
            if veh.year:
                parts.append(str(veh.year))
            if veh.model:
                parts.append(veh.model)
            if veh.trim_id:
                parts.append(veh.trim_id.name)
            base = " ".join(parts) if parts else (veh.vin or _("New Vehicle"))
            veh.display_name = base

    @api.depends("ownership_ids.role", "ownership_ids.active", "ownership_ids.partner_id")
    def _compute_primary_owner(self):
        for veh in self:
            primary = veh.ownership_ids.filtered(lambda o: o.active and o.role == "primary_driver")
            veh.primary_owner_id = primary[:1].partner_id.id if primary else False

    # ------------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------------
    def action_decode_vin(self):
        """Stub for NHTSA vPIC decode. Real implementation in alfa_core_app_api Sprint 11."""
        self.ensure_one()
        self.message_post(
            body=_("VIN decode requested for %s. NHTSA vPIC integration ships in Sprint 11.")
            % self.vin
        )
        return True
