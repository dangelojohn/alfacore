# SPDX-License-Identifier: LGPL-3.0-only
"""Umbrella + journey-surface controllers.

- /alfacore/sim                          landing index
- /alfacore/sim/journey/<surface>        four journey surfaces

Live data resolves explicitly via env.ref('alfa_core.partner_dangelo').sudo()
so admin-as-viewer sees John's records, not admin's empty data.
"""

from odoo import http
from odoo.http import request

# JOURNEY_GROUPS = "alfa_core.group_user,alfa_core.group_advisor,alfa_core.group_manager"  (gating removed)

JOURNEY_SURFACES = {
    "relationship-tape": "alfa_core_ui_sim.relationship_tape",
    "blueprint-authoring": "alfa_core_ui_sim.blueprint_authoring",
    "configurator": "alfa_core_ui_sim.journey_configurator",
    "safety-critical": "alfa_core_ui_sim.safety_critical",
}


class AlfacoreUiSim(http.Controller):
    @http.route("/alfacore/sim", type="http", auth="user", website=True)
    def sim_index(self, **kw):
        return request.render(
            "alfa_core_ui_sim.landing_index",
            {
                "surfaces": self._surface_catalog(),
            },
        )

    @http.route(
        "/alfacore/sim/journey/<string:surface>",
        type="http",
        auth="user",
        website=True,
    )
    def journey(self, surface, mockup=None, **kw):
        template = JOURNEY_SURFACES.get(surface)
        if not template:
            return request.render(
                "alfa_core_ui_sim.surface_not_found",
                {"surface": surface, "known": list(JOURNEY_SURFACES.keys())},
                status=404,
            )

        # Per journey: build a live context, fall back to mockup if records
        # missing on this DB.
        if surface == "relationship-tape":
            ctx = self._mockup_relationship_tape() if mockup else self._live_relationship_tape()
        elif surface == "blueprint-authoring":
            ctx = self._mockup_blueprint() if mockup else self._live_blueprint()
        elif surface == "configurator":
            ctx = self._mockup_configurator() if mockup else self._live_configurator()
        elif surface == "safety-critical":
            ctx = self._mockup_safety_critical() if mockup else self._live_safety_critical()
        else:
            ctx = {}

        return request.render(
            template,
            {
                "ctx": ctx,
                "mockup": bool(mockup),
                "surface_slug": surface,
            },
        )

    # ------------------------------------------------------------------------
    # Catalog
    # ------------------------------------------------------------------------
    def _surface_catalog(self):
        return {
            "pwa": [
                {
                    "slug": "onboarding",
                    "name": "Onboarding",
                    "summary": "First-run setup flow",
                    "url": "/alfacore/sim/pwa/onboarding",
                },
                {
                    "slug": "digital-garage",
                    "name": "Digital Garage",
                    "summary": "Vehicle home — recalls + prefs + next service",
                    "url": "/alfacore/sim/pwa/digital-garage",
                },
                {
                    "slug": "scan-in-progress",
                    "name": "Scan in Progress",
                    "summary": "Live OBD-II scan with DTC + PID streaming",
                    "url": "/alfacore/sim/pwa/scan-in-progress",
                },
                {
                    "slug": "diagnosis",
                    "name": "Diagnosis",
                    "summary": "Rule-based diagnosis report with ZDE indicator",
                    "url": "/alfacore/sim/pwa/diagnosis",
                },
            ],
            "ops": [
                {
                    "slug": "technician-tablet",
                    "name": "Technician Tablet",
                    "summary": "Active job, operations, parts",
                    "url": "/alfacore/sim/ops/technician-tablet",
                },
                {
                    "slug": "advisor-cockpit",
                    "name": "Advisor Cockpit",
                    "summary": "KPI board + live queue + alerts",
                    "url": "/alfacore/sim/ops/advisor-cockpit",
                },
                {
                    "slug": "pro-review-queue",
                    "name": "Pro Review Queue",
                    "summary": "Filterable diagnosis-report review queue",
                    "url": "/alfacore/sim/ops/pro-review-queue",
                },
                {
                    "slug": "loaner-gantt",
                    "name": "Loaner Gantt",
                    "summary": "7-day allocation timeline by vehicle",
                    "url": "/alfacore/sim/ops/loaner-gantt",
                },
            ],
            "journey": [
                {
                    "slug": "relationship-tape",
                    "name": "Relationship Tape",
                    "summary": "Customer-record timeline across modules",
                    "url": "/alfacore/sim/journey/relationship-tape",
                },
                {
                    "slug": "blueprint-authoring",
                    "name": "Blueprint Authoring",
                    "summary": "Inspection template editor with versioning",
                    "url": "/alfacore/sim/journey/blueprint-authoring",
                },
                {
                    "slug": "configurator",
                    "name": "Configurator",
                    "summary": "Cascade flow with rule evaluation trail",
                    "url": "/alfacore/sim/journey/configurator",
                },
                {
                    "slug": "safety-critical",
                    "name": "Safety-Critical Path",
                    "summary": "Do-not-drive recall acknowledgement flow",
                    "url": "/alfacore/sim/journey/safety-critical",
                },
            ],
        }

    # ------------------------------------------------------------------------
    # Live data builders
    # ------------------------------------------------------------------------
    def _demo_partner(self):
        return request.env.ref("alfa_core.partner_dangelo", raise_if_not_found=False)

    def _live_relationship_tape(self):
        partner = self._demo_partner()
        if not partner:
            return self._mockup_relationship_tape()
        partner = partner.sudo()
        events = []
        # Subscriptions
        for sub in partner.subscription_ids:
            events.append(
                {
                    "when": str(sub.create_date.date() if sub.create_date else "—"),
                    "type": "subscription",
                    "title": f"Subscribed: {sub.plan_id.name}",
                    "detail": sub.state,
                }
            )
        # Diagnosis reports
        Report = request.env["alfa_core_diagnosis.report"].sudo()
        for r in Report.search([("partner_id", "=", partner.id)], limit=10):
            events.append(
                {
                    "when": str(r.create_date.date() if r.create_date else "—"),
                    "type": "diagnosis",
                    "title": f"Diagnosis: {r.name}",
                    "detail": f"{r.severity or '—'} · {int((r.confidence or 0) * 100)}%",
                }
            )
        # Inspections
        Insp = request.env["alfa_core_inspection.inspection"].sudo()
        for i in Insp.search([("vehicle_id.ownership_ids.partner_id", "=", partner.id)], limit=10):
            events.append(
                {
                    "when": str(i.create_date.date() if i.create_date else "—"),
                    "type": "inspection",
                    "title": f"Inspection: {i.name}",
                    "detail": f"{i.state}",
                }
            )
        events.sort(key=lambda e: e["when"], reverse=True)
        return {
            "partner": {
                "name": partner.display_name,
                "tier": getattr(partner, "customer_tier", "—") or "—",
                "lifetime_spend": getattr(partner, "lifetime_spend", 0) or 0,
                "since": str(partner.alfa_core_signup_date)
                if hasattr(partner, "alfa_core_signup_date") and partner.alfa_core_signup_date
                else "—",
            },
            "events": events
            or [{"when": "—", "type": "info", "title": "No recorded events yet", "detail": ""}],
        }

    def _mockup_relationship_tape(self):
        return {
            "partner": {
                "name": "John D'Angelo",
                "tier": "gold",
                "lifetime_spend": 18420,
                "since": "2022-10-15",
            },
            "events": [
                {
                    "when": "2026-05-12",
                    "type": "diagnosis",
                    "title": "Diagnosis: AC-DX-2026-000001",
                    "detail": "warn · 78%",
                },
                {
                    "when": "2026-05-12",
                    "type": "inspection",
                    "title": "Inspection: Spring Readiness",
                    "detail": "pending_review",
                },
                {
                    "when": "2026-04-30",
                    "type": "subscription",
                    "title": "Renewed Premium subscription",
                    "detail": "active",
                },
                {
                    "when": "2024-08-12",
                    "type": "service",
                    "title": "Annual service · oil + filter",
                    "detail": "closed · $385",
                },
            ],
        }

    def _live_blueprint(self):
        Template = request.env["alfa_core_inspection.template"].sudo()
        templates = Template.search([("state", "=", "published")], limit=8)
        if not templates:
            return self._mockup_blueprint()
        # Use the first published template as the focal one
        focal = templates[0]
        return {
            "templates": [
                {
                    "name": t.name,
                    "code": t.code,
                    "version": t.version,
                    "item_count": t.item_count,
                    "state": t.state,
                }
                for t in templates
            ],
            "focal": {
                "name": focal.name,
                "code": focal.code,
                "version": focal.version,
                "description": focal.description or "",
                "duration_min": focal.estimated_duration_minutes,
                "items": [
                    {
                        "sequence": item.sequence,
                        "name": item.name,
                        "category": item.category,
                        "measurement_type": item.measurement_type,
                        "is_safety_critical": item.is_safety_critical,
                    }
                    for item in focal.item_ids[:20]
                ],
            },
        }

    def _mockup_blueprint(self):
        return {
            "templates": [
                {
                    "name": "Spring Readiness · 18-Point",
                    "code": "spring_readiness",
                    "version": 1,
                    "item_count": 8,
                    "state": "published",
                },
                {
                    "name": "Track Day Prep · Quadrifoglio",
                    "code": "track_prep_qv",
                    "version": 1,
                    "item_count": 4,
                    "state": "published",
                },
            ],
            "focal": {
                "name": "Spring Readiness · 18-Point",
                "code": "spring_readiness",
                "version": 1,
                "description": "Post-winter inspection.",
                "duration_min": 45,
                "items": [
                    {
                        "sequence": 10,
                        "name": "Front brake pad thickness",
                        "category": "brakes",
                        "measurement_type": "measurement",
                        "is_safety_critical": True,
                    },
                    {
                        "sequence": 20,
                        "name": "Rear brake pad thickness",
                        "category": "brakes",
                        "measurement_type": "measurement",
                        "is_safety_critical": True,
                    },
                    {
                        "sequence": 30,
                        "name": "Brake fluid moisture %",
                        "category": "fluids",
                        "measurement_type": "measurement",
                        "is_safety_critical": True,
                    },
                    {
                        "sequence": 40,
                        "name": "Tire tread depth",
                        "category": "tires",
                        "measurement_type": "measurement",
                        "is_safety_critical": True,
                    },
                ],
            },
        }

    def _live_configurator(self):
        session = request.env.ref(
            "alfa_core_configurator.session_dangelo_spring",
            raise_if_not_found=False,
        )
        if not session:
            return self._mockup_configurator()
        session = session.sudo()
        return {
            "session": {
                "name": session.name,
                "blueprint": session.blueprint_code,
                "state": session.state,
                "vehicle": session.vehicle_id.display_name,
            },
            "signals": [
                {
                    "type": s.signal_type,
                    "weight": s.weight,
                    "confidence": s.confidence,
                    "source": s.source_reference or "",
                }
                for s in session.signal_ids[:10]
            ],
            "ledger": [
                {
                    "type": entry.entry_type,
                    "name": entry.name,
                    "explanation": entry.explanation or "",
                }
                for entry in session.ledger_ids[-15:]
            ],
        }

    def _mockup_configurator(self):
        return {
            "session": {
                "name": "AC-CFG-2026-000001",
                "blueprint": "spring_service",
                "state": "active",
                "vehicle": "2018 Stelvio Ti · ZASFAKBN3J7C12345",
            },
            "signals": [
                {
                    "type": "mileage_interval",
                    "weight": 0.85,
                    "confidence": 0.95,
                    "source": "last_mileage_km=89247",
                },
                {"type": "dtc", "weight": 0.78, "confidence": 0.78, "source": "P0301, P0507"},
                {
                    "type": "season",
                    "weight": 0.55,
                    "confidence": 0.95,
                    "source": "post-winter window",
                },
            ],
            "ledger": [
                {
                    "type": "rule_evaluated",
                    "name": "Track Prep — Pro tier only",
                    "explanation": "Did not match: subscription = premium",
                },
                {
                    "type": "rule_evaluated",
                    "name": "Loaner included — Premium+",
                    "explanation": "Matched: subscription in (premium, pro)",
                },
                {
                    "type": "option_hidden",
                    "name": "track_prep_inspection",
                    "explanation": "Resolved to hide (rules: 1, conflicts: 0)",
                },
                {
                    "type": "recommendation_made",
                    "name": "complimentary_loaner",
                    "explanation": "Resolved to recommend (score 0.65)",
                },
            ],
        }

    def _live_safety_critical(self):
        Campaign = request.env["alfa_core_campaign.campaign"].sudo()
        crit = Campaign.search([("severity", "=", "safety_critical")], limit=1)
        if not crit:
            return self._mockup_safety_critical()
        c = crit[0]
        Target = request.env["alfa_core_campaign.target"].sudo()
        targets = Target.search([("campaign_id", "=", c.id)], limit=5)
        return {
            "campaign": {
                "name": c.name,
                "source_id": c.source_id,
                "severity": c.severity,
                "affected_components": c.affected_components or "",
                "risk_summary": c.risk_summary or "",
                "remedy_summary": c.remedy_summary or "",
            },
            "targets": [
                {
                    "vehicle": t.vehicle_id.display_name,
                    "partner": t.partner_id.display_name if t.partner_id else "—",
                    "state": t.state,
                    "attempts": t.notification_attempts,
                }
                for t in targets
            ],
        }

    def _mockup_safety_critical(self):
        return {
            "campaign": {
                "name": "Stelvio fuel pump driver module — do not drive",
                "source_id": "DEMO-23V456000",
                "severity": "safety_critical",
                "affected_components": "Fuel System, Gasoline: Delivery: Fuel Pump",
                "risk_summary": "Fuel pump driver module may fail intermittently, causing stalling at low speed. Increased crash risk.",
                "remedy_summary": "PARK IT — do not drive until remedied.\nDealer will replace the fuel pump driver module free of charge.",
            },
            "targets": [
                {
                    "vehicle": "2018 Stelvio Ti · ZASFAKBN3J7C12345",
                    "partner": "John D'Angelo",
                    "state": "notified",
                    "attempts": 2,
                },
                {
                    "vehicle": "2019 Stelvio · ZASFAKBN3K7C00045",
                    "partner": "G. Marchetti",
                    "state": "scheduled",
                    "attempts": 1,
                },
            ],
        }
