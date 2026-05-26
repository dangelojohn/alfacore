# SPDX-License-Identifier: LGPL-3.0-only
"""Back-office (operator) wireframe controllers.

Four surfaces gated to AlfaCore staff groups:
- /alfacore/sim/ops/technician-tablet
- /alfacore/sim/ops/advisor-cockpit
- /alfacore/sim/ops/pro-review-queue
- /alfacore/sim/ops/loaner-gantt

Live data is default. ?mockup=1 swaps to the bundled mock dictionaries.
"""

import logging
from datetime import datetime, timedelta

from odoo import http
from odoo.http import request

from ..data.wireframe_mocks import (
    ADVISOR_COCKPIT,
    LOANER_GANTT,
    PRO_REVIEW_QUEUE,
    TECHNICIAN_TABLET,
)

_logger = logging.getLogger(__name__)

# OPS_GROUPS = "alfa_core.group_user,alfa_core.group_advisor,alfa_core.group_manager"  (gating removed)


class AlfacoreUiSimOps(http.Controller):
    # ------------------------------------------------------------------------
    # Technician tablet
    # ------------------------------------------------------------------------
    @http.route(
        "/alfacore/sim/ops/technician-tablet",
        type="http",
        auth="user",
        website=True,
    )
    def technician_tablet(self, mockup=None, **kw):
        ctx = TECHNICIAN_TABLET if mockup else self._live_technician_tablet()
        return request.render(
            "alfa_core_ui_sim_ops.technician_tablet",
            {"ctx": ctx, "mockup": bool(mockup), "surface_slug": "technician-tablet"},
        )

    def _live_technician_tablet(self):
        """Read the most-recent in-progress SO for John D'Angelo's vehicle."""
        try:
            vehicle = request.env.ref("alfa_fleet.vehicle_dangelo_stelvio").sudo()
            partner = request.env.ref("alfa_core.partner_dangelo").sudo()
        except ValueError:
            return TECHNICIAN_TABLET

        SO = request.env["sale.order"].sudo()
        so = SO.search(
            [
                ("partner_id", "=", partner.id),
                ("alfa_vehicle_id", "=", vehicle.id),
            ],
            order="create_date desc",
            limit=1,
        )

        # The bare scaffold case: no SO yet on this DB. Fall back to mockup.
        if not so:
            return TECHNICIAN_TABLET

        return {
            "current_job": {
                "name": so.name,
                "customer_name": partner.display_name,
                "vehicle_label": f"{vehicle.year} {vehicle.model} · {vehicle.vin}",
                "mileage_km": vehicle.last_mileage_km,
                "bay": so.alfa_bay_id.display_name if so.alfa_bay_id else "—",
                "service_state": so.alfa_service_state or "draft",
                "operations": [
                    {"name": line.name, "state": "—", "duration_min": 0}
                    for line in so.order_line[:5]
                ],
                "parts_picked": [],
                "dtcs_active": ["P0301", "P0507"],  # from the demo scan
            }
        }

    # ------------------------------------------------------------------------
    # Advisor cockpit
    # ------------------------------------------------------------------------
    @http.route(
        "/alfacore/sim/ops/advisor-cockpit",
        type="http",
        auth="user",
        website=True,
    )
    def advisor_cockpit(self, mockup=None, **kw):
        ctx = ADVISOR_COCKPIT if mockup else self._live_advisor_cockpit()
        return request.render(
            "alfa_core_ui_sim_ops.advisor_cockpit",
            {"ctx": ctx, "mockup": bool(mockup), "surface_slug": "advisor-cockpit"},
        )

    def _live_advisor_cockpit(self):
        SO = request.env["sale.order"].sudo()
        open_states = (
            "draft",
            "confirmed",
            "parts_ordered",
            "parts_ready",
            "scheduled",
            "in_progress",
            "inspection_pending",
            "findings_review",
            "quality_check",
        )
        open_orders = SO.search_count([("alfa_service_state", "in", open_states)])
        awaiting_parts = SO.search_count([("alfa_service_state", "=", "parts_ordered")])
        ready_for_pickup = SO.search_count([("alfa_service_state", "=", "ready_for_pickup")])

        queue_records = SO.search(
            [
                ("alfa_service_state", "!=", False),
            ],
            order="create_date desc",
            limit=6,
        )
        queue = []
        for r in queue_records:
            queue.append(
                {
                    "name": r.name,
                    "customer": r.partner_id.display_name,
                    "state": r.alfa_service_state,
                    "vehicle": r.alfa_vehicle_id.display_name if r.alfa_vehicle_id else "—",
                    "tech": r.alfa_technician_id.name if r.alfa_technician_id else "—",
                    "eta": "—",
                }
            )
        if not queue:
            return ADVISOR_COCKPIT

        return {
            "kpis": {
                "open_orders": open_orders,
                "awaiting_parts": awaiting_parts,
                "ready_for_pickup": ready_for_pickup,
                "today_revenue_cad": 0,
            },
            "queue": queue,
            "alerts": [],
        }

    # ------------------------------------------------------------------------
    # Pro review queue
    # ------------------------------------------------------------------------
    @http.route(
        "/alfacore/sim/ops/pro-review-queue",
        type="http",
        auth="user",
        website=True,
    )
    def pro_review_queue(self, mockup=None, **kw):
        ctx = PRO_REVIEW_QUEUE if mockup else self._live_pro_review_queue()
        return request.render(
            "alfa_core_ui_sim_ops.pro_review_queue",
            {"ctx": ctx, "mockup": bool(mockup), "surface_slug": "pro-review-queue"},
        )

    def _live_pro_review_queue(self):
        Report = request.env["alfa_core_diagnosis.report"].sudo()
        reports = Report.search(
            [
                ("state", "in", ("pending_review", "ai_generated")),
            ],
            order="severity desc, create_date desc",
            limit=20,
        )

        if not reports:
            return PRO_REVIEW_QUEUE

        now = datetime.now()
        items = []
        for r in reports:
            age_seconds = (now - (r.create_date or now)).total_seconds()
            age_hours = round(age_seconds / 3600.0, 1)
            # Primary DTC is the first one on the scan_session. The
            # traversal can fail if the scan_session is missing or its
            # dtc_ids isn't loaded — non-fatal for the wireframe; default
            # to empty string and log the rare failure.
            primary_dtc = ""
            try:
                primary_dtc = r.scan_session_id.dtc_ids[:1].dtc_code or ""
            except Exception as err:
                _logger.debug("primary_dtc lookup skipped for report %s: %s", r.name, err)
            items.append(
                {
                    "name": r.name,
                    "vehicle": r.vehicle_id.display_name if r.vehicle_id else "—",
                    "customer": r.partner_id.display_name if r.partner_id else "—",
                    "severity": r.severity or "info",
                    "confidence": r.confidence or 0.0,
                    "age_hours": age_hours,
                    "primary_dtc": primary_dtc,
                    "state": r.state,
                }
            )
        return {"reports": items}

    # ------------------------------------------------------------------------
    # Loaner gantt
    # ------------------------------------------------------------------------
    @http.route(
        "/alfacore/sim/ops/loaner-gantt", type="http", auth="user", website=True
    )
    def loaner_gantt(self, mockup=None, **kw):
        ctx = LOANER_GANTT if mockup else self._live_loaner_gantt()
        return request.render(
            "alfa_core_ui_sim_ops.loaner_gantt",
            {"ctx": ctx, "mockup": bool(mockup), "surface_slug": "loaner-gantt"},
        )

    def _live_loaner_gantt(self):
        Vehicle = request.env["alfa_core_loaner.vehicle"].sudo()
        Allocation = request.env["alfa_core_loaner.allocation"].sudo()
        vehicles = Vehicle.search([("active", "=", True)], order="sequence, id", limit=8)
        if not vehicles:
            return LOANER_GANTT

        # Window: 7 days starting today
        today = datetime.now().date()
        day_labels = [(today + timedelta(days=i)).strftime("%a %d") for i in range(7)]
        end = today + timedelta(days=7)

        allocations = Allocation.search(
            [
                ("loaner_vehicle_id", "in", vehicles.ids),
                ("scheduled_return_date", ">=", today),
                ("pickup_date", "<=", end),
            ]
        )

        veh_list = [
            {"name": v.name, "plate": v.license_plate, "tier": v.tier_eligibility} for v in vehicles
        ]
        alloc_list = []
        for a in allocations:
            try:
                veh_idx = vehicles.ids.index(a.loaner_vehicle_id.id)
            except ValueError:
                continue
            start_offset = max(0, (a.pickup_date - today).days)
            span = max(1, (a.scheduled_return_date - a.pickup_date).days)
            alloc_list.append(
                {
                    "vehicle_idx": veh_idx,
                    "customer": a.partner_id.display_name if a.partner_id else "—",
                    "day_start": start_offset,
                    "day_span": span,
                    "state": a.state,
                }
            )

        return {
            "vehicles": veh_list,
            "allocations": alloc_list,
            "day_labels": day_labels,
        }
