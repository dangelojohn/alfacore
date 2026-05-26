# SPDX-License-Identifier: LGPL-3.0-only
"""Loaner allocation — vehicle assigned to customer for date range.

Pattern 1 — finite pipeline stages: scheduled → active → completed.
Pattern 9 — every state change logged.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AlfaLoanerAllocation(models.Model):
    _name = "alfa_core_loaner.allocation"
    _description = "Loaner Allocation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "pickup_date desc, id desc"
    _rec_name = "name"

    name = fields.Char(required=True, copy=False, readonly=True, default=lambda s: _("New"))
    loaner_vehicle_id = fields.Many2one(
        "alfa_core_loaner.vehicle", string="Loaner", required=True, tracking=True, index=True
    )
    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True, index=True
    )
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Service Order",
        help="The service that triggered this loaner assignment.",
    )
    customer_vehicle_id = fields.Many2one(
        "alfa_fleet.vehicle",
        string="Customer Vehicle In Service",
        help="The vehicle the customer left with us.",
    )

    pickup_date = fields.Date(required=True, tracking=True)
    scheduled_return_date = fields.Date(required=True, tracking=True)
    actual_return_date = fields.Date(tracking=True)
    days_scheduled = fields.Integer(compute="_compute_days", store=True)
    days_actual = fields.Integer(compute="_compute_days", store=True)
    days_overage = fields.Integer(compute="_compute_days", store=True)

    pickup_mileage_km = fields.Integer(string="Pickup Mileage")
    return_mileage_km = fields.Integer(string="Return Mileage")
    miles_driven = fields.Integer(compute="_compute_miles", store=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("scheduled", "Scheduled"),
            ("active", "Active (in use)"),
            ("returned", "Returned"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )

    # E-signature integration lives in the optional `alfa_core_loaner_sign`
    # sub-module, which depends on Odoo Enterprise's `sign`. When installed,
    # it adds `sign_request_id` + `sign_status` fields via _inherit and
    # overrides action_activate / action_cancel to enforce signature flow.

    pickup_report_id = fields.Many2one(
        "alfa_core_loaner.condition_report", string="Pickup Condition Report"
    )
    return_report_id = fields.Many2one(
        "alfa_core_loaner.condition_report", string="Return Condition Report"
    )

    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "alfa_core_loaner.allocation"
                ) or _("New")
        return super().create(vals_list)

    @api.constrains("pickup_date", "scheduled_return_date", "actual_return_date")
    def _check_dates(self):
        for a in self:
            if (
                a.scheduled_return_date
                and a.pickup_date
                and a.scheduled_return_date < a.pickup_date
            ):
                raise ValidationError(_("Scheduled return cannot precede pickup."))
            if a.actual_return_date and a.pickup_date and a.actual_return_date < a.pickup_date:
                raise ValidationError(_("Actual return cannot precede pickup."))

    @api.depends("pickup_date", "scheduled_return_date", "actual_return_date")
    def _compute_days(self):
        for a in self:
            if a.pickup_date and a.scheduled_return_date:
                a.days_scheduled = (a.scheduled_return_date - a.pickup_date).days
            else:
                a.days_scheduled = 0
            if a.pickup_date and a.actual_return_date:
                a.days_actual = (a.actual_return_date - a.pickup_date).days
            else:
                a.days_actual = 0
            a.days_overage = max(0, a.days_actual - a.days_scheduled)

    @api.depends("pickup_mileage_km", "return_mileage_km")
    def _compute_miles(self):
        for a in self:
            if a.pickup_mileage_km and a.return_mileage_km:
                a.miles_driven = a.return_mileage_km - a.pickup_mileage_km
            else:
                a.miles_driven = 0

    # ------------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------------
    def action_schedule(self):
        """Draft → Scheduled. Sends signature request."""
        for a in self:
            if a.state != "draft":
                raise UserError(_("Can only schedule a draft allocation."))
            if a.loaner_vehicle_id.state != "available":
                raise UserError(_("Loaner %s is not available.") % a.loaner_vehicle_id.name)
            a.state = "scheduled"
            a.loaner_vehicle_id.state = "allocated"
            a.message_post(body=_("Allocation scheduled for %s.") % a.pickup_date)

    # Send-for-signature, signature-status sync, and the sync cron live in
    # `alfa_core_loaner_sign` (depends on Enterprise's `sign` module).

    def action_activate(self):
        """Scheduled → Active (customer picked up the loaner).

        When `alfa_core_loaner_sign` is installed, it overrides this method
        to additionally require sign_status == "signed".
        """
        for a in self:
            if a.state != "scheduled":
                raise UserError(_("Can only activate a scheduled allocation."))
            if not a.pickup_report_id:
                raise UserError(_("Pickup condition report required."))
            a.state = "active"
            a.message_post(body=_("Loaner picked up by customer."))

    def action_return(self):
        """Active → Returned (customer brought it back)."""
        for a in self:
            if a.state != "active":
                raise UserError(_("Can only return an active allocation."))
            if not a.return_report_id:
                raise UserError(_("Return condition report required."))
            if not a.actual_return_date:
                a.actual_return_date = fields.Date.context_today(self)
            a.state = "returned"
            a.loaner_vehicle_id.state = "available"
            if a.return_mileage_km:
                a.loaner_vehicle_id.current_mileage_km = a.return_mileage_km
            a.message_post(body=_("Loaner returned. Driven %d km.") % a.miles_driven)

    def action_complete(self):
        """Returned → Completed (final reconciliation done)."""
        for a in self:
            if a.state != "returned":
                raise UserError(_("Can only complete a returned allocation."))
            a.state = "completed"
            a.message_post(body=_("Allocation closed."))

    def action_cancel(self):
        """Cancel the allocation. When `alfa_core_loaner_sign` is installed,
        it overrides this to also cancel the linked sign.request."""
        for a in self:
            if a.state in ("completed", "cancelled"):
                continue
            a.state = "cancelled"
            if (
                a.loaner_vehicle_id.state == "allocated"
                and a.loaner_vehicle_id.current_allocation_id == a
            ):
                a.loaner_vehicle_id.state = "available"
            a.message_post(body=_("Allocation cancelled."))
