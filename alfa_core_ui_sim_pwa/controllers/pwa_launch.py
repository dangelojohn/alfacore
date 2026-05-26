# SPDX-License-Identifier: LGPL-3.0-only
"""PWA wireframe launch controller.

Issues a short-lived demo JWT through alfa_core_app_api.jwt_secret_manager
(NOT a parallel signing key — same rotation surface as production), then
redirects the browser to the static PWA index page with the token in the
URL fragment.

Why URL fragment instead of cookie or query string:
- Fragments aren't sent server-side on subsequent fetches
- Avoids accidental log capture of the JWT
- Appropriate for short-lived (5min) demo tokens

The static HTML pages read window.location.hash, extract the token, and
use it as `Authorization: Bearer <jwt>` against /api/v1/*.

In live-data mode, the controller mints the JWT for the demo partner
(alfa_core.partner_dangelo) explicitly rather than the request user,
so an admin previewing the customer view sees John's records, not
admin's empty data.

In mockup mode (?mockup=1), no JWT is issued; the static page is
expected to use its bundled MOCKUP_DATA and skip the /api/v1/* fetches.
"""

import logging
from datetime import datetime, timedelta

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# Demo JWT TTL — five minutes is enough for a stakeholder demo without
# leaving a long-lived bearer in someone's browser fragment.
DEMO_JWT_TTL_MINUTES = 5

PWA_SURFACES = ["onboarding", "digital-garage", "scan-in-progress", "diagnosis"]


class AlfacoreUiSimPwa(http.Controller):
    @http.route("/alfacore/sim/pwa", type="http", auth="user", website=True)
    def pwa_index(self, mockup=None, **kw):
        """Default landing — redirects to digital-garage as the canonical start."""
        return self._launch("digital-garage", mockup)

    @http.route(
        "/alfacore/sim/pwa/<string:surface>",
        type="http",
        auth="user",
        website=True,
    )
    def pwa_surface(self, surface, mockup=None, **kw):
        if surface not in PWA_SURFACES:
            return request.render(
                "alfa_core_ui_sim_pwa.surface_not_found",
                {"surface": surface, "known": PWA_SURFACES},
                status=404,
            )
        return self._launch(surface, mockup)

    # ------------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------------
    def _launch(self, surface, mockup):
        """Mint a JWT (or skip in mockup mode) and redirect to the static page."""
        static_url = f"/alfa_core_ui_sim_pwa/static/src/pwa/{surface}.html"

        if mockup:
            # Mockup mode — no JWT needed; static page uses bundled MOCKUP_DATA
            return request.redirect(f"{static_url}?mockup=1", local=True)

        try:
            token = self._issue_demo_jwt()
        except Exception as e:
            _logger.warning("Demo JWT issuance failed: %s", e)
            return request.render(
                "alfa_core_ui_sim_pwa.jwt_issuance_failed",
                {"error": str(e)},
                status=500,
            )

        # URL fragment — not sent server-side on subsequent fetches
        return request.redirect(f"{static_url}#token={token}", local=True)

    def _issue_demo_jwt(self):
        """Mint a short-lived JWT for the demo partner (John D'Angelo).

        Goes through alfa_core_app_api.jwt_secret_manager so key rotation
        in prod stays in sync with sim — no parallel signing key.
        """
        try:
            import jwt
        except ImportError as err:
            raise RuntimeError(
                "pyjwt is not installed in the Odoo container. "
                "See section 1.5 of the Claude Code handoff doc."
            ) from err

        # Resolve demo partner explicitly
        demo_partner = request.env.ref("alfa_core.partner_dangelo", raise_if_not_found=False)
        if not demo_partner:
            raise RuntimeError(
                "Demo partner alfa_core.partner_dangelo not found. "
                "Verify the alfa_core module installed with demo data."
            )

        # Issue a token record via the existing pipeline
        Token = request.env["alfa_core_app_api.token"].sudo()
        token_rec = Token.issue_for_partner(
            demo_partner.id,
            scope="pwa",
            ttl_days=1,
        )
        # Override the token expiry to short-lived for demo purposes
        token_rec.expires_at = datetime.utcnow() + timedelta(minutes=DEMO_JWT_TTL_MINUTES)

        # Sign through the rotation-aware manager
        Manager = request.env["alfa_core_app_api.jwt_secret_manager"].sudo()
        secret = Manager.get_current_secret()
        if not secret:
            raise RuntimeError(
                "JWT secret not configured. Initialize via Manager.action_rotate_secret()."
            )

        now = datetime.utcnow()
        payload = {
            "sub": str(demo_partner.id),
            "jti": token_rec.jti,
            "scope": "pwa",
            "iat": int(now.timestamp()),
            "exp": int(token_rec.expires_at.timestamp()),
            "demo": True,
        }
        return jwt.encode(payload, secret, algorithm="HS256")
