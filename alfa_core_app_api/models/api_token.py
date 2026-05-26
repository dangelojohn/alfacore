# SPDX-License-Identifier: LGPL-3.0-only
"""JWT token registry — issued to the companion PWA on login.

Records what tokens are alive, their owner, expiry, and last use. Allows
revocation, audit, and rotation. The actual JWT signing/verifying uses pyjwt
and a server-side secret.
"""

import secrets
from datetime import timedelta

from odoo import api, fields, models


class AlfaApiToken(models.Model):
    _name = "alfa_core_app_api.token"
    _description = "AlfaCore API Token"
    _order = "issued_at desc"
    _rec_name = "jti"

    jti = fields.Char(
        string="JWT ID (jti)",
        required=True,
        copy=False,
        index=True,
        help="Unique token identifier — used to revoke.",
    )
    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade", index=True)
    issued_at = fields.Datetime(default=fields.Datetime.now, required=True)
    expires_at = fields.Datetime(required=True)
    last_used_at = fields.Datetime()
    last_used_ip = fields.Char()
    scope = fields.Char(
        default="pwa", help="Token scope: 'pwa' (companion app), 'admin' (advisor tools)."
    )
    state = fields.Selection(
        [
            ("active", "Active"),
            ("revoked", "Revoked"),
            ("expired", "Expired"),
        ],
        default="active",
        required=True,
    )

    _jti_uniq = models.Constraint(
        "UNIQUE(jti)",
        "JWT ID must be unique.",
    )

    @api.model
    def issue_for_partner(self, partner_id, scope="pwa", ttl_days=30):
        """Create a new token record. Caller (controller) does the JWT signing
        and returns the bearer string."""
        jti = secrets.token_urlsafe(16)
        rec = self.create(
            {
                "jti": jti,
                "partner_id": partner_id,
                "expires_at": fields.Datetime.now() + timedelta(days=ttl_days),
                "scope": scope,
            }
        )
        return rec

    def action_revoke(self):
        for t in self:
            t.state = "revoked"

    @api.model
    def expire_stale(self):
        """Cron entry — sweeps expired tokens."""
        now = fields.Datetime.now()
        stale = self.search(
            [
                ("state", "=", "active"),
                ("expires_at", "<", now),
            ]
        )
        stale.write({"state": "expired"})
        return len(stale)
