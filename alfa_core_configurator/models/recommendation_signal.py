# SPDX-License-Identifier: LGPL-3.0-only
"""Recommendation signal — input to the configurator's recommendation cascade.

Signals are typed inputs: scan-derived DTCs, mileage thresholds, calendar
intervals, customer preferences, technician observations. Each signal has
weight, expiry, and provenance.
"""

from odoo import fields, models


class AlfaConfiguratorSignal(models.Model):
    _name = "alfa_core_configurator.signal"
    _description = "Configurator Recommendation Signal"
    _order = "session_id, weight desc, id"

    session_id = fields.Many2one(
        "alfa_core_configurator.session", required=True, ondelete="cascade", index=True
    )
    signal_type = fields.Selection(
        [
            ("dtc", "DTC"),
            ("mileage_interval", "Mileage Interval"),
            ("time_interval", "Time Interval"),
            ("customer_preference", "Customer Preference"),
            ("technician_observation", "Technician Observation"),
            ("recall_open", "Open Recall"),
            ("tsb_match", "TSB Match"),
            ("season", "Seasonal"),
        ],
        required=True,
    )
    name = fields.Char(required=True)
    value = fields.Char(help="Signal value (e.g. DTC code, mileage number, preference key).")
    weight = fields.Float(default=1.0, help="0.0-1.0. Drives recommendation ranking.")
    confidence = fields.Float(default=1.0, help="How sure we are this signal is real / current.")
    source_reference = fields.Char(
        help="ID of source record (scan_session, diagnosis_report, etc.)"
    )
    captured_at = fields.Datetime(default=fields.Datetime.now)
    expires_at = fields.Datetime(
        help="Signals can stale (e.g. mileage signal expires when next reading comes in)."
    )
