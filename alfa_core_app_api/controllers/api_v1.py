# SPDX-License-Identifier: LGPL-3.0-only
"""AlfaCore companion PWA REST API — /api/v1/*.

Endpoints:
- POST /api/v1/auth                          issue JWT for a portal user
- POST /api/v1/scans                         upload a scan session
- GET  /api/v1/diagnoses/<id>                retrieve diagnosis report
- GET  /api/v1/vehicles/<vin>/preferences    vehicle preferences
- GET  /api/v1/vehicles/<vin>/recalls        open recall campaigns

All routes are rate-limited:
- /api/v1/auth        10 attempts/min per IP, 5 burst (credential-stuffing brake)
- read endpoints      120 req/min per token, 30 burst
                      + 600 req/min per IP, 100 burst (DDoS brake)

JWT signing uses the dual-secret rotation pattern (see
alfa_core_app_api.jwt_secret_manager). Tokens signed under the previous
secret are accepted during the 30-day grace window.

Pattern 10 — rate limits return 429 with a Retry-After header. The
limiter is in-memory per-worker; production with multi-worker or
multi-replica wants Redis-backed shared state.
"""

import json
import logging
from datetime import datetime

from odoo import fields, http
from odoo.exceptions import AccessDenied
from odoo.http import Response, request

from ..models.rate_limiter import limiter

_logger = logging.getLogger(__name__)


def _json_response(data, status=200, headers=None):
    response_headers = {"Content-Type": "application/json"}
    if headers:
        response_headers.update(headers)
    return Response(
        json.dumps(data, default=str),
        status=status,
        headers=list(response_headers.items()),
    )


def _client_ip():
    """Best-effort source IP — checks X-Forwarded-For first (when proxy_mode
    is on), falls back to direct connection."""
    fwd = request.httprequest.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.httprequest.remote_addr or "unknown"


def _rate_limit_check(profile, key):
    """Apply a rate limit. Returns None if allowed, or a 429 response."""
    allowed, retry_after = limiter.check(profile, key)
    if allowed:
        return None
    return _json_response(
        {
            "error": "rate_limit_exceeded",
            "retry_after_seconds": round(retry_after, 1),
        },
        status=429,
        headers={"Retry-After": str(int(retry_after) + 1)},
    )


def _require_token(func):
    """Decorator: extract & verify JWT from Authorization header, attach
    partner to request. Applies the api_read + api_ip rate limits."""

    def wrapper(self, *args, **kwargs):
        try:
            import jwt  # pyjwt
        except ImportError:
            return _json_response({"error": "pyjwt_not_installed"}, status=500)

        auth_header = request.httprequest.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return _json_response({"error": "missing_bearer_token"}, status=401)
        token = auth_header[7:]

        # Verify (with rotation fallback)
        Manager = request.env["alfa_core_app_api.jwt_secret_manager"].sudo()
        try:
            payload = Manager.verify_token(token)
        except jwt.ExpiredSignatureError:
            return _json_response({"error": "token_expired"}, status=401)
        except jwt.InvalidTokenError:
            return _json_response({"error": "invalid_token"}, status=401)

        # Verify token record is still active
        Token = request.env["alfa_core_app_api.token"].sudo()
        token_rec = Token.search(
            [
                ("jti", "=", payload.get("jti")),
                ("state", "=", "active"),
            ],
            limit=1,
        )
        if not token_rec:
            return _json_response({"error": "token_revoked_or_unknown"}, status=401)

        # Apply rate limits: per-token AND per-IP
        ip = _client_ip()
        ip_rejected = _rate_limit_check("api_ip", ip)
        if ip_rejected:
            return ip_rejected
        token_rejected = _rate_limit_check("api_read", str(token_rec.partner_id.id))
        if token_rejected:
            return token_rejected

        # Update last_used
        token_rec.write(
            {
                "last_used_at": fields.Datetime.now(),
                "last_used_ip": ip,
            }
        )
        request.api_partner_id = token_rec.partner_id.id
        request.api_token_rec = token_rec
        return func(self, *args, **kwargs)

    return wrapper


class AlfaApiV1(http.Controller):
    # ------------------------------------------------------------------------
    # POST /api/v1/auth — issue JWT (rate-limited by IP)
    # ------------------------------------------------------------------------
    @http.route("/api/v1/auth", type="jsonrpc", auth="public", methods=["POST"], csrf=False)
    def auth(self, login=None, password=None, **kw):
        # Tight per-IP rate limit on auth — slows credential stuffing
        ip = _client_ip()
        allowed, retry_after = limiter.check("auth", ip)
        if not allowed:
            return {
                "error": "rate_limit_exceeded",
                "retry_after_seconds": round(retry_after, 1),
            }
        if not login or not password:
            return {"error": "missing_credentials"}
        try:
            import jwt
        except ImportError:
            return {"error": "pyjwt_not_installed"}

        try:
            credential = {"type": "password", "login": login, "password": password}
            uid = request.env["res.users"].authenticate(request.session.db, credential, {})
            if not uid.get("uid"):
                raise AccessDenied()
            user = request.env["res.users"].sudo().browse(uid["uid"])
        except AccessDenied:
            return {"error": "invalid_credentials"}

        # Issue token record
        Token = request.env["alfa_core_app_api.token"].sudo()
        token_rec = Token.issue_for_partner(user.partner_id.id, scope="pwa")

        # Sign JWT using the CURRENT secret (rotation: previous secret is
        # only used during verify, never to sign new tokens)
        Manager = request.env["alfa_core_app_api.jwt_secret_manager"].sudo()
        secret = Manager.get_current_secret()
        if not secret:
            return {"error": "jwt_secret_not_configured"}

        now = datetime.utcnow()
        payload = {
            "sub": str(user.partner_id.id),
            "jti": token_rec.jti,
            "scope": "pwa",
            "iat": int(now.timestamp()),
            "exp": int(token_rec.expires_at.timestamp()),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        return {
            "token": token,
            "expires_at": token_rec.expires_at.isoformat(),
            "partner": {
                "id": user.partner_id.id,
                "name": user.partner_id.name,
            },
        }

    # ------------------------------------------------------------------------
    # POST /api/v1/scans — upload a scan session
    # ------------------------------------------------------------------------
    @http.route("/api/v1/scans", type="jsonrpc", auth="public", methods=["POST"], csrf=False)
    @_require_token
    def upload_scan(
        self,
        vehicle_vin=None,
        started_at=None,
        ended_at=None,
        modules_scanned=None,
        battery_voltage=None,
        mileage_at_scan=None,
        dtcs=None,
        pids=None,
        **kw,
    ):
        if not vehicle_vin:
            return {"error": "vehicle_vin_required"}
        Vehicle = request.env["alfa_fleet.vehicle"].sudo()
        veh = Vehicle.search([("vin", "=", vehicle_vin.upper())], limit=1)
        if not veh:
            return {"error": "vehicle_not_found", "vin": vehicle_vin}
        owners = veh.ownership_ids.filtered("active").mapped("partner_id.id")
        if request.api_partner_id not in owners:
            return {"error": "not_authorized_for_this_vehicle"}

        Device = request.env["alfa_core_scanner.device"].sudo()
        device = Device.search(
            [
                ("partner_id", "=", request.api_partner_id),
                ("vehicle_id", "=", veh.id),
            ],
            limit=1,
        )
        if not device:
            return {"error": "no_paired_device_for_vehicle"}

        Session = request.env["alfa_core_scanner.scan_session"].sudo()
        session = Session.create(
            {
                "vehicle_id": veh.id,
                "device_id": device.id,
                "started_at": started_at,
                "ended_at": ended_at,
                "modules_scanned": modules_scanned,
                "battery_voltage": battery_voltage,
                "mileage_at_scan": mileage_at_scan,
                "state": "uploaded",
            }
        )
        DTC = request.env["alfa_core_scanner.scan_dtc"].sudo()
        for d in dtcs or []:
            DTC.create(
                {
                    "scan_session_id": session.id,
                    "dtc_code": d.get("code"),
                    "dtc_status": d.get("status", "active"),
                    "module_source": d.get("module"),
                    "freeze_frame_data": d.get("freeze_frame"),
                    "raw_payload": d.get("raw"),
                }
            )
        PID = request.env["alfa_core_scanner.scan_pid"].sudo()
        for p in pids or []:
            PID.create(
                {
                    "scan_session_id": session.id,
                    "pid_id": p.get("pid"),
                    "pid_name": p.get("name"),
                    "value": p.get("value"),
                    "units": p.get("units"),
                }
            )
        return {
            "session_id": session.id,
            "name": session.name,
            "dtc_count": session.dtc_count,
        }

    # ------------------------------------------------------------------------
    # GET /api/v1/diagnoses/<id>
    # ------------------------------------------------------------------------
    @http.route(
        "/api/v1/diagnoses/<int:report_id>", type="http", auth="public", methods=["GET"], csrf=False
    )
    @_require_token
    def get_diagnosis(self, report_id, **kw):
        Report = request.env["alfa_core_diagnosis.report"].sudo()
        report = Report.browse(report_id).exists()
        if not report:
            return _json_response({"error": "not_found"}, status=404)
        if report.partner_id.id != request.api_partner_id:
            return _json_response({"error": "not_authorized"}, status=403)
        return _json_response(
            {
                "id": report.id,
                "name": report.name,
                "vehicle_vin": report.vehicle_id.vin,
                "state": report.state,
                "confidence": report.confidence,
                "severity": report.severity,
                "summary": report.summary,
                "recommendations": [
                    {
                        "id": r.id,
                        "name": r.name,
                        "description": r.description,
                        "action_type": r.action_type,
                        "confidence": r.confidence,
                    }
                    for r in report.recommendation_ids
                ],
            }
        )

    # ------------------------------------------------------------------------
    # GET /api/v1/vehicles/<vin>/preferences
    # ------------------------------------------------------------------------
    @http.route(
        "/api/v1/vehicles/<string:vin>/preferences",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    @_require_token
    def get_preferences(self, vin, **kw):
        Vehicle = request.env["alfa_fleet.vehicle"].sudo()
        veh = Vehicle.search([("vin", "=", vin.upper())], limit=1)
        if not veh:
            return _json_response({"error": "vehicle_not_found"}, status=404)
        owners = veh.ownership_ids.filtered("active").mapped("partner_id.id")
        if request.api_partner_id not in owners:
            return _json_response({"error": "not_authorized"}, status=403)
        return _json_response(
            {
                "vin": veh.vin,
                "preferences": [
                    {
                        "category": p.category,
                        "name": p.name,
                        "spec": p.spec,
                        "brand_preference": p.brand_preference,
                    }
                    for p in veh.preference_ids.filtered("active")
                ],
            }
        )

    # ------------------------------------------------------------------------
    # GET /api/v1/vehicles/<vin>/recalls — open recall campaigns
    # ------------------------------------------------------------------------
    @http.route(
        "/api/v1/vehicles/<string:vin>/recalls",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    @_require_token
    def get_recalls(self, vin, **kw):
        """Return all open (non-serviced) recall campaign targets for the
        specified vehicle. The companion PWA renders these on the Digital
        Garage screen with red dots / banners for safety_critical entries.
        """
        Vehicle = request.env["alfa_fleet.vehicle"].sudo()
        veh = Vehicle.search([("vin", "=", vin.upper())], limit=1)
        if not veh:
            return _json_response({"error": "vehicle_not_found"}, status=404)
        owners = veh.ownership_ids.filtered("active").mapped("partner_id.id")
        if request.api_partner_id not in owners:
            return _json_response({"error": "not_authorized"}, status=403)

        Target = request.env["alfa_core_campaign.target"].sudo()
        targets = Target.search(
            [
                ("vehicle_id", "=", veh.id),
                ("state", "in", ("identified", "notified", "acknowledged", "scheduled")),
            ]
        )

        return _json_response(
            {
                "vin": veh.vin,
                "open_recall_count": len(targets),
                "do_not_drive": any(t.campaign_id.severity == "safety_critical" for t in targets),
                "recalls": [
                    {
                        "campaign_id": t.campaign_id.id,
                        "campaign_name": t.campaign_id.name,
                        "source": t.campaign_id.source,
                        "source_id": t.campaign_id.source_id,
                        "source_url": t.campaign_id.source_url,
                        "severity": t.campaign_id.severity,
                        "campaign_type": t.campaign_id.campaign_type,
                        "affected_components": t.campaign_id.affected_components,
                        "risk_summary": t.campaign_id.risk_summary,
                        "remedy_summary": t.campaign_id.remedy_summary,
                        "estimated_remedy_hours": t.campaign_id.estimated_remedy_hours,
                        "issued_date": (
                            t.campaign_id.issued_date.isoformat()
                            if t.campaign_id.issued_date
                            else None
                        ),
                        "target_state": t.state,
                        "last_notified_at": (
                            t.last_notified_at.isoformat() if t.last_notified_at else None
                        ),
                        "notification_attempts": t.notification_attempts,
                        "scheduled_so": (t.scheduled_so_id.name if t.scheduled_so_id else None),
                    }
                    for t in targets
                ],
            }
        )
