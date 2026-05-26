# SPDX-License-Identifier: LGPL-3.0-only
"""JWT signing secret rotation management.

Two ir.config_parameter slots:
  alfa_core_app_api.jwt_secret           current (active) signing secret
  alfa_core_app_api.jwt_secret_previous  previous secret during grace window

JWT verification tries `jwt_secret` first. If signature check fails, falls
back to `jwt_secret_previous`. This lets tokens issued before rotation
continue to work until they naturally expire (default ttl_days=30).

Rotation procedure (automated via `action_rotate_secret`):
  1. Read current `jwt_secret` value
  2. Write it to `jwt_secret_previous`
  3. Generate new secret via secrets.token_urlsafe(32)
  4. Write new secret to `jwt_secret`
  5. Log rotation event

Grace period cleanup (manual or cron):
  After 30 days (max token lifetime), all tokens signed under the previous
  secret are guaranteed expired. The `action_clear_previous_secret` empties
  the previous slot. Or run via the cron — `cron_clear_stale_previous`.

Pattern 9 — every rotation event posts a chatter message on the AlfaCore
config record (or a dedicated rotation log) so the security history is
auditable. Pattern 10 — if the previous slot is non-empty for more than
30 days, the cron logs a warning that the grace window has elapsed and the
old secret should be cleared.
"""

import logging
import secrets
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


CURRENT_KEY = "alfa_core_app_api.jwt_secret"
PREVIOUS_KEY = "alfa_core_app_api.jwt_secret_previous"
ROTATED_AT_KEY = "alfa_core_app_api.jwt_secret_rotated_at"
# Grace window — after this, the previous secret is no longer needed
GRACE_DAYS = 30


class AlfaJwtSecretManager(models.AbstractModel):
    """Singleton-ish manager. Not a stored model — just a model namespace
    for the action methods we want to expose to the Settings UI."""

    _name = "alfa_core_app_api.jwt_secret_manager"
    _description = "JWT Secret Manager"

    @api.model
    def get_current_secret(self):
        """Return the current signing secret. Used by issue and verify."""
        return self.env["ir.config_parameter"].sudo().get_param(CURRENT_KEY)

    @api.model
    def get_previous_secret(self):
        """Return the previous secret if one is set, else None."""
        val = self.env["ir.config_parameter"].sudo().get_param(PREVIOUS_KEY)
        return val or None

    @api.model
    def verify_token(self, token):
        """Verify a JWT against current secret, falling back to previous.

        Returns the decoded payload on success. Raises jwt.InvalidTokenError
        (or a subclass) on failure under BOTH secrets.
        """
        import jwt

        current = self.get_current_secret()
        if not current:
            raise jwt.InvalidTokenError("No JWT secret configured")

        try:
            return jwt.decode(token, current, algorithms=["HS256"])
        except jwt.InvalidSignatureError:
            previous = self.get_previous_secret()
            if not previous:
                raise
            try:
                payload = jwt.decode(token, previous, algorithms=["HS256"])
                _logger.info(
                    "JWT verified against previous secret (jti=%s). "
                    "Token was issued before the most recent rotation.",
                    payload.get("jti"),
                )
                return payload
            except jwt.InvalidTokenError as err:
                raise jwt.InvalidSignatureError(
                    "Token signature does not match current or previous secret"
                ) from err

    @api.model
    def action_rotate_secret(self):
        """Rotate the JWT signing secret.

        Steps:
          1. Move current → previous
          2. Generate new secret
          3. Write new secret as current
          4. Stamp the rotation timestamp
        """
        ICP = self.env["ir.config_parameter"].sudo()
        current = ICP.get_param(CURRENT_KEY) or ""

        # Don't rotate to the empty string — if no current is configured,
        # this is the first-time setup, not a rotation.
        if not current or current.startswith("CHANGE_ME") or current.startswith("dev-"):
            new_secret = secrets.token_urlsafe(32)
            ICP.set_param(CURRENT_KEY, new_secret)
            ICP.set_param(ROTATED_AT_KEY, fields.Datetime.now().isoformat())
            _logger.warning(
                "JWT secret initialized for the first time. Issuance now signs "
                "with the new secret. No previous secret stored."
            )
            return {"status": "initialized", "rotated_at": ICP.get_param(ROTATED_AT_KEY)}

        # True rotation
        ICP.set_param(PREVIOUS_KEY, current)
        new_secret = secrets.token_urlsafe(32)
        ICP.set_param(CURRENT_KEY, new_secret)
        ICP.set_param(ROTATED_AT_KEY, fields.Datetime.now().isoformat())
        _logger.warning(
            "JWT secret rotated. Previous secret retained for %d days for "
            "in-flight tokens. Clear with action_clear_previous_secret after grace.",
            GRACE_DAYS,
        )
        return {
            "status": "rotated",
            "rotated_at": ICP.get_param(ROTATED_AT_KEY),
            "grace_until": (fields.Datetime.now() + timedelta(days=GRACE_DAYS)).isoformat(),
        }

    @api.model
    def action_clear_previous_secret(self):
        """Clear the previous secret slot. Run after the grace window has
        elapsed (default 30 days)."""
        ICP = self.env["ir.config_parameter"].sudo()
        had = bool(ICP.get_param(PREVIOUS_KEY))
        ICP.set_param(PREVIOUS_KEY, "")
        _logger.warning(
            "JWT previous-secret slot cleared. %s",
            "Old tokens can no longer be verified." if had else "(Was already empty.)",
        )
        return {"status": "cleared", "had_previous": had}

    @api.model
    def cron_clear_stale_previous(self):
        """Cron entry — auto-clear the previous secret if rotation is older
        than the grace window. Conservative: only clears if rotation timestamp
        is set and more than GRACE_DAYS old. If timestamp is missing, leaves
        the secret alone and logs a warning (operator decides)."""
        ICP = self.env["ir.config_parameter"].sudo()
        if not ICP.get_param(PREVIOUS_KEY):
            return {"status": "no_previous"}
        rotated_at_str = ICP.get_param(ROTATED_AT_KEY)
        if not rotated_at_str:
            _logger.warning(
                "JWT previous secret is set but rotated_at timestamp missing. "
                "Cannot auto-clear safely. Use action_clear_previous_secret "
                "manually after confirming the grace window has elapsed."
            )
            return {"status": "no_timestamp"}
        try:
            rotated_at = fields.Datetime.from_string(rotated_at_str.replace("T", " ").split(".")[0])
        except Exception:
            return {"status": "bad_timestamp"}
        age = fields.Datetime.now() - rotated_at
        if age >= timedelta(days=GRACE_DAYS):
            return self.action_clear_previous_secret()
        return {
            "status": "still_in_grace",
            "days_remaining": (timedelta(days=GRACE_DAYS) - age).days,
        }
