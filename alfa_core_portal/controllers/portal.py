# SPDX-License-Identifier: LGPL-3.0-only
"""Customer portal routes for AlfaCore.

Extends Odoo's CustomerPortal to surface:
- /my/vehicles            Vehicle list + detail (Digital Garage)
- /my/diagnoses           Diagnosis reports + detail
- /my/inspections         Inspections + per-finding approval
- /my/loaners             Active and historical loaner allocations

Row-level security is enforced via ir.rule (security/ir_rules.xml).
Portal user only sees records where partner_id maps to them.
"""

from odoo import _, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


class AlfaCorePortal(CustomerPortal):
    """Extends the stock CustomerPortal with AlfaCore surfaces."""

    # ------------------------------------------------------------------------
    # /my landing — counters
    # ------------------------------------------------------------------------
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if "vehicle_count" in counters:
            values["vehicle_count"] = request.env["alfa_fleet.vehicle"].search_count(
                [
                    ("ownership_ids.partner_id", "=", partner.id),
                    ("ownership_ids.active", "=", True),
                ]
            )
        if "diagnosis_count" in counters:
            values["diagnosis_count"] = request.env["alfa_core_diagnosis.report"].search_count(
                [
                    ("partner_id", "=", partner.id),
                    ("state", "in", ("reviewed", "delivered")),
                ]
            )
        if "inspection_pending_count" in counters:
            values["inspection_pending_count"] = request.env[
                "alfa_core_inspection.inspection"
            ].search_count(
                [
                    ("vehicle_id.ownership_ids.partner_id", "=", partner.id),
                    ("state", "=", "customer_review"),
                ]
            )
        if "loaner_count" in counters:
            values["loaner_count"] = request.env["alfa_core_loaner.allocation"].search_count(
                [
                    ("partner_id", "=", partner.id),
                    ("state", "in", ("scheduled", "active")),
                ]
            )
        return values

    # ------------------------------------------------------------------------
    # /my/vehicles
    # ------------------------------------------------------------------------
    @http.route(
        ["/my/vehicles", "/my/vehicles/page/<int:page>"], type="http", auth="user", website=True
    )
    def portal_my_vehicles(self, page=1, sortby=None, **kw):
        partner = request.env.user.partner_id
        Vehicle = request.env["alfa_fleet.vehicle"]
        domain = [
            ("ownership_ids.partner_id", "=", partner.id),
            ("ownership_ids.active", "=", True),
        ]
        searchbar_sortings = {
            "year_desc": {"label": _("Newest first"), "order": "year desc"},
            "model": {"label": _("Model"), "order": "model"},
            "mileage": {"label": _("Mileage"), "order": "last_mileage_km desc"},
        }
        sortby = sortby or "year_desc"
        order = searchbar_sortings[sortby]["order"]
        total = Vehicle.search_count(domain)
        pager = portal_pager(
            url="/my/vehicles",
            url_args={"sortby": sortby},
            total=total,
            page=page,
            step=self._items_per_page,
        )
        vehicles = Vehicle.search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )
        return request.render(
            "alfa_core_portal.portal_my_vehicles",
            {
                "vehicles": vehicles,
                "page_name": "vehicle",
                "pager": pager,
                "sortby": sortby,
                "searchbar_sortings": searchbar_sortings,
                "default_url": "/my/vehicles",
            },
        )

    @http.route("/my/vehicles/<int:vehicle_id>", type="http", auth="user", website=True)
    def portal_my_vehicle_detail(self, vehicle_id, **kw):
        try:
            vehicle_sudo = self._document_check_access("alfa_fleet.vehicle", vehicle_id)
        except (AccessError, MissingError):
            return request.redirect("/my")
        return request.render(
            "alfa_core_portal.portal_my_vehicle_detail",
            {
                "vehicle": vehicle_sudo,
                "page_name": "vehicle_detail",
            },
        )

    # ------------------------------------------------------------------------
    # /my/diagnoses
    # ------------------------------------------------------------------------
    @http.route(
        ["/my/diagnoses", "/my/diagnoses/page/<int:page>"], type="http", auth="user", website=True
    )
    def portal_my_diagnoses(self, page=1, **kw):
        partner = request.env.user.partner_id
        Report = request.env["alfa_core_diagnosis.report"]
        domain = [
            ("partner_id", "=", partner.id),
            ("state", "in", ("reviewed", "delivered")),
        ]
        total = Report.search_count(domain)
        pager = portal_pager(
            url="/my/diagnoses",
            total=total,
            page=page,
            step=self._items_per_page,
        )
        reports = Report.search(
            domain, order="create_date desc", limit=self._items_per_page, offset=pager["offset"]
        )
        return request.render(
            "alfa_core_portal.portal_my_diagnoses",
            {
                "reports": reports,
                "page_name": "diagnosis",
                "pager": pager,
                "default_url": "/my/diagnoses",
            },
        )

    @http.route("/my/diagnoses/<int:report_id>", type="http", auth="user", website=True)
    def portal_my_diagnosis_detail(self, report_id, **kw):
        try:
            report_sudo = self._document_check_access("alfa_core_diagnosis.report", report_id)
        except (AccessError, MissingError):
            return request.redirect("/my")
        return request.render(
            "alfa_core_portal.portal_my_diagnosis_detail",
            {
                "report": report_sudo,
                "page_name": "diagnosis_detail",
            },
        )

    # ------------------------------------------------------------------------
    # /my/inspections — customer-approval-gated findings
    # ------------------------------------------------------------------------
    @http.route(
        ["/my/inspections", "/my/inspections/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_inspections(self, page=1, **kw):
        partner = request.env.user.partner_id
        Inspection = request.env["alfa_core_inspection.inspection"]
        domain = [
            ("vehicle_id.ownership_ids.partner_id", "=", partner.id),
            (
                "state",
                "in",
                ("customer_review", "approved", "partially_approved", "declined", "applied"),
            ),
        ]
        total = Inspection.search_count(domain)
        pager = portal_pager(
            url="/my/inspections",
            total=total,
            page=page,
            step=self._items_per_page,
        )
        inspections = Inspection.search(
            domain, order="create_date desc", limit=self._items_per_page, offset=pager["offset"]
        )
        return request.render(
            "alfa_core_portal.portal_my_inspections",
            {
                "inspections": inspections,
                "page_name": "inspection",
                "pager": pager,
                "default_url": "/my/inspections",
            },
        )

    @http.route("/my/inspections/<int:inspection_id>", type="http", auth="user", website=True)
    def portal_my_inspection_detail(self, inspection_id, **kw):
        try:
            inspection_sudo = self._document_check_access(
                "alfa_core_inspection.inspection", inspection_id
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        return request.render(
            "alfa_core_portal.portal_my_inspection_detail",
            {
                "inspection": inspection_sudo,
                "page_name": "inspection_detail",
            },
        )

    @http.route(
        "/my/inspections/<int:inspection_id>/decide",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_inspection_decide(self, inspection_id, **post):
        """Customer submits per-finding approve/decline decisions."""
        try:
            inspection_sudo = self._document_check_access(
                "alfa_core_inspection.inspection", inspection_id
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        if inspection_sudo.state != "customer_review":
            return request.redirect(f"/my/inspections/{inspection_id}")
        # POST: finding_<id> = "approved" | "declined" | "defer"
        for finding in inspection_sudo.finding_ids:
            key = f"finding_{finding.id}"
            decision = post.get(key)
            if decision in ("approved", "declined", "defer"):
                finding.customer_decision = decision
                from odoo import fields

                finding.customer_decision_at = fields.Datetime.now()
        return request.redirect(f"/my/inspections/{inspection_id}?decision_recorded=1")

    # ------------------------------------------------------------------------
    # /my/loaners
    # ------------------------------------------------------------------------
    @http.route(
        ["/my/loaners", "/my/loaners/page/<int:page>"], type="http", auth="user", website=True
    )
    def portal_my_loaners(self, page=1, **kw):
        partner = request.env.user.partner_id
        Allocation = request.env["alfa_core_loaner.allocation"]
        domain = [("partner_id", "=", partner.id)]
        total = Allocation.search_count(domain)
        pager = portal_pager(
            url="/my/loaners",
            total=total,
            page=page,
            step=self._items_per_page,
        )
        allocations = Allocation.search(
            domain, order="pickup_date desc", limit=self._items_per_page, offset=pager["offset"]
        )
        return request.render(
            "alfa_core_portal.portal_my_loaners",
            {
                "allocations": allocations,
                "page_name": "loaner",
                "pager": pager,
                "default_url": "/my/loaners",
            },
        )
