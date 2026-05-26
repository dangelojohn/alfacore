# SPDX-License-Identifier: LGPL-3.0-only
"""Reusable inspection templates.

JTBD §3.2.4 — inspections are not ad-hoc checklists. They're versioned,
named templates that an advisor selects when authoring a SO. Templates
capture institutional knowledge ('what we always check on a Stelvio
returning from winter').
"""

from odoo import _, api, fields, models


class AlfaInspectionTemplate(models.Model):
    _name = "alfa_core_inspection.template"
    _description = "Inspection Template"
    _order = "sequence, name"
    _inherit = ["mail.thread"]

    name = fields.Char(
        required=True,
        translate=True,
        tracking=True,
        help="e.g. 'Pre-purchase 100-point', 'Spring readiness', 'Track day prep'.",
    )
    code = fields.Char(
        required=True,
        copy=False,
        help="Stable identifier. Used for API and Configurator referencing.",
    )
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=10)
    version = fields.Integer(
        default=1,
        tracking=True,
        help="Pattern 12 — versioned content. Published templates are immutable; "
        "amendments create a new version.",
    )
    item_ids = fields.One2many(
        "alfa_core_inspection.template_item", "template_id", string="Inspection Items"
    )
    item_count = fields.Integer(compute="_compute_item_count", store=True)
    fits_platform_ids = fields.Many2many(
        "alfa_fleet.platform",
        relation="alfa_inspection_tmpl_platform_rel",
        string="Applies to Platforms",
    )
    estimated_duration_minutes = fields.Integer(default=30)
    requires_lift = fields.Boolean(
        default=True, help="Inspection needs a lift bay; affects scheduling."
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("published", "Published"),
            ("retired", "Retired"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    active = fields.Boolean(default=True)

    _code_version_uniq = models.Constraint(
        "UNIQUE(code, version)",
        "Template code + version combination must be unique.",
    )

    @api.depends("item_ids")
    def _compute_item_count(self):
        for tmpl in self:
            tmpl.item_count = len(tmpl.item_ids)

    def action_publish(self):
        for tmpl in self:
            if tmpl.state != "draft":
                continue
            if not tmpl.item_ids:
                from odoo.exceptions import UserError

                raise UserError(_("Cannot publish template with no items."))
            tmpl.state = "published"
            tmpl.message_post(body=_("Template published as version %d.") % tmpl.version)

    def action_retire(self):
        for tmpl in self:
            tmpl.state = "retired"
            tmpl.message_post(body=_("Template retired."))


class AlfaInspectionTemplateItem(models.Model):
    _name = "alfa_core_inspection.template_item"
    _description = "Inspection Template Item"
    _order = "template_id, sequence, id"

    template_id = fields.Many2one(
        "alfa_core_inspection.template", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(
        required=True, translate=True, help="e.g. 'Front brake pad thickness', 'CV boot integrity'."
    )
    description = fields.Text(
        translate=True, help="Inspection criteria — what to look for, threshold values."
    )
    sequence = fields.Integer(default=10)
    category = fields.Selection(
        [
            ("brakes", "Brakes"),
            ("suspension", "Suspension"),
            ("steering", "Steering"),
            ("drivetrain", "Drivetrain"),
            ("tires", "Tires"),
            ("fluids", "Fluids"),
            ("electrical", "Electrical"),
            ("body", "Body & Exterior"),
            ("interior", "Interior"),
            ("safety", "Safety Systems"),
            ("other", "Other"),
        ],
        required=True,
        default="other",
    )
    measurement_type = fields.Selection(
        [
            ("pass_fail", "Pass / Fail"),
            ("measurement", "Measurement (with units)"),
            ("photo", "Photo required"),
            ("text", "Free text"),
        ],
        required=True,
        default="pass_fail",
    )
    measurement_units = fields.Char(help="If measurement_type=measurement, e.g. 'mm', 'PSI', '%%'.")
    threshold_pass = fields.Float(help="For measurements: value at or above which item passes.")
    threshold_warn = fields.Float(
        help="For measurements: value at or above which item warns. Below = fail."
    )
    is_safety_critical = fields.Boolean(
        help="Safety-critical items fail the whole inspection on a fail finding."
    )
