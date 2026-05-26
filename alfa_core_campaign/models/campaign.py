# SPDX-License-Identifier: LGPL-3.0-only
"""Recall / TSB campaign master record.

Aggregates campaigns from authoritative sources (primarily NHTSA for North
America, plus future Transport Canada + manufacturer feeds). Each campaign
identifies affected vehicles by VIN range, model year, and platform.

Per Service Plan §7 — recall posture is proactive. We pull NHTSA daily,
match to our customer fleet, and trigger notifications. We never wait for
customers to find out from the dealer.
"""

from odoo import _, api, fields, models


class AlfaCampaign(models.Model):
    _name = "alfa_core_campaign.campaign"
    _description = "Recall / TSB Campaign"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "issued_date desc, id desc"

    name = fields.Char(
        required=True,
        tracking=True,
        help="Internal display name, e.g. '2018 Stelvio fuel pump recall'.",
    )
    campaign_type = fields.Selection(
        [
            ("safety_recall", "Safety Recall"),
            ("emissions_recall", "Emissions Recall"),
            ("service_campaign", "Service Campaign"),
            ("tsb", "Technical Service Bulletin"),
            ("warranty_extension", "Warranty Extension"),
        ],
        required=True,
        default="safety_recall",
        tracking=True,
    )

    source = fields.Selection(
        [
            ("nhtsa", "NHTSA (US)"),
            ("transport_canada", "Transport Canada"),
            ("manufacturer", "Manufacturer Direct"),
            ("other", "Other"),
        ],
        required=True,
        default="nhtsa",
        index=True,
    )
    source_id = fields.Char(
        string="Source Campaign ID", index=True, help="e.g. NHTSA Campaign Number '23V456000'."
    )
    source_url = fields.Char(string="Source URL")

    manufacturer = fields.Char(default="Alfa Romeo")
    affected_components = fields.Char(
        help="Brief component list, e.g. 'Fuel Pump', 'Brake Booster'."
    )
    risk_summary = fields.Text(translate=True, help="Customer-facing risk explanation.")
    remedy_summary = fields.Text(translate=True, help="What the dealer will do to remedy.")
    estimated_remedy_hours = fields.Float()

    severity = fields.Selection(
        [
            ("safety_critical", "Safety Critical (do-not-drive)"),
            ("high", "High"),
            ("medium", "Medium"),
            ("low", "Low (informational)"),
        ],
        required=True,
        default="medium",
        tracking=True,
    )

    issued_date = fields.Date(tracking=True)
    received_at = fields.Datetime(
        default=fields.Datetime.now, help="When we received this campaign from the source feed."
    )

    # Affected vehicle criteria
    fits_platform_ids = fields.Many2many(
        "alfa_fleet.platform", relation="alfa_camp_platform_rel", string="Affected Platforms"
    )
    fits_engine_ids = fields.Many2many(
        "alfa_fleet.engine", relation="alfa_camp_engine_rel", string="Affected Engines"
    )
    affected_year_from = fields.Integer()
    affected_year_to = fields.Integer()
    vin_pattern = fields.Char(
        help="VIN matcher (substring or regex). Used by NHTSA for production-range identification."
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("imported", "Imported"),
            ("targeting", "Targeting"),
            ("notifying", "Notifying"),
            ("active", "Active"),
            ("closed", "Closed"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )

    target_ids = fields.One2many(
        "alfa_core_campaign.target", "campaign_id", string="Targeted Vehicles"
    )
    target_count = fields.Integer(compute="_compute_target_stats", store=True)
    notified_count = fields.Integer(compute="_compute_target_stats", store=True)
    serviced_count = fields.Integer(compute="_compute_target_stats", store=True)

    _source_id_uniq = models.Constraint(
        "UNIQUE(source, source_id)",
        "Source campaign ID must be unique per source.",
    )

    @api.depends("target_ids.state")
    def _compute_target_stats(self):
        for c in self:
            c.target_count = len(c.target_ids)
            c.notified_count = len(
                c.target_ids.filtered(lambda t: t.state in ("notified", "scheduled", "serviced"))
            )
            c.serviced_count = len(c.target_ids.filtered(lambda t: t.state == "serviced"))

    def action_target_vehicles(self):
        """Materialize alfa_core_campaign.target rows for affected vehicles."""
        Vehicle = self.env["alfa_fleet.vehicle"]
        Target = self.env["alfa_core_campaign.target"]
        for camp in self:
            domain = []
            if camp.fits_platform_ids:
                domain.append(("platform_id", "in", camp.fits_platform_ids.ids))
            if camp.fits_engine_ids:
                domain.append(("engine_id", "in", camp.fits_engine_ids.ids))
            if camp.affected_year_from:
                domain.append(("year", ">=", camp.affected_year_from))
            if camp.affected_year_to:
                domain.append(("year", "<=", camp.affected_year_to))
            candidates = Vehicle.search(domain)
            # VIN pattern filter — done in Python; postgres regex is awkward.
            if camp.vin_pattern:
                # Bind pattern at lambda-creation time so the closure doesn't
                # capture the loop variable.
                candidates = candidates.filtered(lambda v, p=camp.vin_pattern: p in (v.vin or ""))
            existing_vehicle_ids = camp.target_ids.mapped("vehicle_id.id")
            new_targets = []
            for v in candidates:
                if v.id in existing_vehicle_ids:
                    continue
                new_targets.append(
                    {
                        "campaign_id": camp.id,
                        "vehicle_id": v.id,
                    }
                )
            if new_targets:
                Target.create(new_targets)
            camp.state = "targeting"
            camp.message_post(
                body=_("Targeting complete: %d candidate vehicles, %d new targets.")
                % (len(candidates), len(new_targets))
            )

    def action_close(self):
        for c in self:
            c.state = "closed"
            c.message_post(body=_("Campaign closed."))
