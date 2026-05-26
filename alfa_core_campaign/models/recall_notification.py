# SPDX-License-Identifier: LGPL-3.0-only
"""Customer-facing recall notification record."""

from odoo import fields, models


class AlfaRecallNotification(models.Model):
    _name = "alfa_core_campaign.notification"
    _description = "Recall Customer Notification"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    target_id = fields.Many2one(
        "alfa_core_campaign.target", required=True, ondelete="cascade", index=True
    )
    campaign_id = fields.Many2one(related="target_id.campaign_id", store=True)
    partner_id = fields.Many2one(related="target_id.partner_id", store=True)
    vehicle_id = fields.Many2one(related="target_id.vehicle_id", store=True)

    channel = fields.Selection(
        [
            ("email", "Email"),
            ("sms", "SMS"),
            ("portal", "Portal banner"),
            ("phone", "Phone call"),
            ("mail", "Postal mail"),
        ],
        required=True,
    )
    sent_at = fields.Datetime()
    response = fields.Selection(
        [
            ("none", "No response"),
            ("acknowledged", "Acknowledged"),
            ("scheduled", "Wants to schedule"),
            ("declined", "Declined"),
            ("bounce", "Delivery failed"),
        ],
        default="none",
        tracking=True,
    )
    response_at = fields.Datetime()
    message_text = fields.Text(help="The actual notification body as sent.")

    def action_mark_sent(self):
        for n in self:
            n.sent_at = fields.Datetime.now()
            if n.target_id.state == "identified":
                n.target_id.state = "notified"
            n.target_id.notification_attempts += 1
