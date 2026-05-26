# SPDX-License-Identifier: LGPL-3.0-only
"""Per-vehicle campaign target — one row per (campaign, vehicle) pair.

Tracks the customer's progress: notified → scheduled → serviced (or declined).
"""

from odoo import api, fields, models


class AlfaCampaignTarget(models.Model):
    _name = "alfa_core_campaign.target"
    _description = "Campaign Target Vehicle"
    _inherit = ["mail.thread"]
    _order = "campaign_id, id"

    campaign_id = fields.Many2one(
        "alfa_core_campaign.campaign", required=True, ondelete="cascade", index=True
    )
    vehicle_id = fields.Many2one(
        "alfa_fleet.vehicle", required=True, ondelete="cascade", index=True
    )
    partner_id = fields.Many2one("res.partner", compute="_compute_partner", store=True, index=True)

    state = fields.Selection(
        [
            ("identified", "Identified"),
            ("notified", "Customer Notified"),
            ("acknowledged", "Customer Acknowledged"),
            ("scheduled", "Service Scheduled"),
            ("serviced", "Serviced"),
            ("declined", "Customer Declined"),
            ("unreachable", "Unreachable"),
        ],
        default="identified",
        required=True,
        tracking=True,
        index=True,
    )

    notification_ids = fields.One2many(
        "alfa_core_campaign.notification", "target_id", string="Notifications"
    )
    last_notified_at = fields.Datetime(compute="_compute_last_notified", store=True)
    notification_attempts = fields.Integer(default=0)

    scheduled_so_id = fields.Many2one("sale.order", string="Scheduled Service Order")
    serviced_at = fields.Datetime()

    _camp_vehicle_uniq = models.Constraint(
        "UNIQUE(campaign_id, vehicle_id)",
        "One target row per campaign × vehicle.",
    )

    @api.depends("vehicle_id.ownership_ids.partner_id")
    def _compute_partner(self):
        for t in self:
            primary = t.vehicle_id.ownership_ids.filtered(
                lambda o: o.active and o.role == "primary_driver"
            )
            t.partner_id = primary[:1].partner_id.id if primary else False

    @api.depends("notification_ids.sent_at")
    def _compute_last_notified(self):
        for t in self:
            sent = t.notification_ids.filtered("sent_at")
            t.last_notified_at = max(sent.mapped("sent_at")) if sent else False
