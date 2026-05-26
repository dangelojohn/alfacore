# SPDX-License-Identifier: LGPL-3.0-only
"""Partner extensions for AlfaCore — PIPEDA consent, tier compute, channel preference."""

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # ------------------------------------------------------------------------
    # AlfaCore identity
    # ------------------------------------------------------------------------
    alfa_core_customer = fields.Boolean(
        string="AlfaCore Customer",
        tracking=True,
        help="Marks this partner as an active AlfaCore service customer.",
    )
    alfa_core_signup_date = fields.Datetime(
        string="AlfaCore Signup Date",
        tracking=True,
        help="When this partner first became an AlfaCore customer.",
    )

    # ------------------------------------------------------------------------
    # PIPEDA consent (Service Plan §10)
    # ------------------------------------------------------------------------
    alfa_core_pipeda_consent_version = fields.Char(
        string="PIPEDA Consent Version",
        groups="alfa_core.group_pipeda_officer",
        help="Version identifier of the PIPEDA consent text the partner agreed to.",
    )
    alfa_core_pipeda_consent_date = fields.Datetime(
        string="PIPEDA Consent Date",
        groups="alfa_core.group_pipeda_officer",
        help="When the partner gave PIPEDA consent for the current version.",
    )

    # ------------------------------------------------------------------------
    # Communication preference
    # ------------------------------------------------------------------------
    alfa_core_preferred_channel = fields.Selection(
        selection=[
            ("email", "Email"),
            ("sms", "SMS"),
            ("whatsapp", "WhatsApp"),
            ("portal", "Portal Only"),
        ],
        string="Preferred Channel",
        default="email",
        tracking=True,
        help="Primary channel for AlfaCore communications. WhatsApp deferred to v1.1.",
    )

    # ------------------------------------------------------------------------
    # Customer tier (JTBD Gap Analysis §2.5.4)
    # ------------------------------------------------------------------------
    alfa_core_customer_tier = fields.Selection(
        selection=[
            ("bronze", "Bronze"),
            ("silver", "Silver"),
            ("gold", "Gold"),
            ("platinum", "Platinum"),
        ],
        string="AlfaCore Tier",
        compute="_compute_alfa_core_customer_tier",
        store=True,
        compute_sudo=True,
        help="Computed tier based on tenure and lifetime spend. "
        "Bronze <1yr; Silver 1-3yr or spend>$5K; "
        "Gold 3yr+ or spend>$15K; Platinum 5yr+ and spend>$30K.",
    )
    alfa_core_lifetime_spend = fields.Monetary(
        string="Lifetime Spend",
        compute="_compute_alfa_core_lifetime_spend",
        store=True,
        compute_sudo=True,
        currency_field="currency_id",
        help="Sum of posted customer invoices. Drives tier compute.",
    )

    # ------------------------------------------------------------------------
    # Subscriptions
    # ------------------------------------------------------------------------
    alfa_core_subscription_ids = fields.One2many(
        comodel_name="alfa_core.subscription",
        inverse_name="partner_id",
        string="AlfaCore Subscriptions",
    )
    alfa_core_active_subscription_id = fields.Many2one(
        comodel_name="alfa_core.subscription",
        compute="_compute_active_subscription",
        store=True,
        string="Active Subscription",
    )

    # ------------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------------
    @api.depends(
        "alfa_core_customer",
        "alfa_core_signup_date",
        "alfa_core_lifetime_spend",
    )
    def _compute_alfa_core_customer_tier(self):
        now = fields.Datetime.now()
        for partner in self:
            if not partner.alfa_core_customer or not partner.alfa_core_signup_date:
                partner.alfa_core_customer_tier = False
                continue
            tenure_days = (now - partner.alfa_core_signup_date).days
            tenure_years = tenure_days / 365.25
            spend = partner.alfa_core_lifetime_spend or 0.0
            if tenure_years >= 5 and spend > 30000:
                partner.alfa_core_customer_tier = "platinum"
            elif tenure_years >= 3 or spend > 15000:
                partner.alfa_core_customer_tier = "gold"
            elif tenure_years >= 1 or spend > 5000:
                partner.alfa_core_customer_tier = "silver"
            else:
                partner.alfa_core_customer_tier = "bronze"

    @api.depends("invoice_ids.state", "invoice_ids.amount_total", "invoice_ids.move_type")
    def _compute_alfa_core_lifetime_spend(self):
        for partner in self:
            paid = partner.invoice_ids.filtered(
                lambda inv: inv.state == "posted" and inv.move_type == "out_invoice"
            )
            partner.alfa_core_lifetime_spend = sum(paid.mapped("amount_total"))

    @api.depends("alfa_core_subscription_ids.state")
    def _compute_active_subscription(self):
        for partner in self:
            active = partner.alfa_core_subscription_ids.filtered(
                lambda s: s.state in ("trial", "active")
            )
            partner.alfa_core_active_subscription_id = active[:1].id if active else False

    # ------------------------------------------------------------------------
    # Overrides — auto-stamp signup date
    # ------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("alfa_core_customer") and not vals.get("alfa_core_signup_date"):
                vals["alfa_core_signup_date"] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("alfa_core_customer"):
            for partner in self:
                if not partner.alfa_core_signup_date and "alfa_core_signup_date" not in vals:
                    partner.alfa_core_signup_date = fields.Datetime.now()
        return super().write(vals)
