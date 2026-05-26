# SPDX-License-Identifier: LGPL-3.0-only
"""Loaner condition report — pickup and return snapshots."""

from odoo import fields, models


class AlfaLoanerConditionReport(models.Model):
    _name = "alfa_core_loaner.condition_report"
    _description = "Loaner Condition Report"
    _order = "create_date desc"

    report_type = fields.Selection(
        [
            ("pickup", "Pickup"),
            ("return", "Return"),
        ],
        required=True,
    )
    allocation_id = fields.Many2one("alfa_core_loaner.allocation", ondelete="cascade", index=True)
    inspector_id = fields.Many2one("hr.employee", string="Inspector")
    inspection_date = fields.Datetime(default=fields.Datetime.now, required=True)

    exterior_condition = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("damaged", "Damaged"),
        ],
        required=True,
        default="excellent",
    )
    interior_condition = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("damaged", "Damaged"),
        ],
        required=True,
        default="excellent",
    )
    fuel_level = fields.Selection(
        [
            ("full", "Full"),
            ("3_4", "3/4"),
            ("1_2", "1/2"),
            ("1_4", "1/4"),
            ("empty", "Empty"),
        ],
        required=True,
        default="full",
    )
    mileage_km = fields.Integer(required=True)
    photo_front = fields.Image(max_width=1920, max_height=1080)
    photo_rear = fields.Image(max_width=1920, max_height=1080)
    photo_left = fields.Image(max_width=1920, max_height=1080)
    photo_right = fields.Image(max_width=1920, max_height=1080)
    photo_interior = fields.Image(max_width=1920, max_height=1080)
    damage_notes = fields.Text()
    signature_data = fields.Binary(
        string="Customer Signature", help="Base64 signature blob captured at pickup/return."
    )
