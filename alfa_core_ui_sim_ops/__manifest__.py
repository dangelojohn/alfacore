# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — UI Sim · Operations",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore — Internal Tools",
    "summary": "Operator wireframes (4 surfaces) — Technician Tablet, Advisor Cockpit, Pro Review Queue, Loaner Gantt",
    "description": """
Operator-facing wireframes for stakeholder demos.

Four QWeb surfaces gated to AlfaCore staff groups (group_user, group_advisor,
group_manager):
- /alfacore/sim/ops/technician-tablet
- /alfacore/sim/ops/advisor-cockpit
- /alfacore/sim/ops/pro-review-queue
- /alfacore/sim/ops/loaner-gantt

Live data by default, ?mockup=1 toggle for design review.
""",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": [
        "alfa_core",
        "alfa_fleet",
        "alfa_service",
        "alfa_core_loaner",
        "alfa_core_diagnosis",
        # `website` provides web.frontend_layout used by ops_templates.xml.
        "website",
    ],
    "data": [
        "views/ops_templates.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "alfa_core_ui_sim_ops/static/src/scss/design_system.scss",
            "alfa_core_ui_sim_ops/static/src/js/sim_interactions.js",
        ],
        "web.assets_frontend": [
            "alfa_core_ui_sim_ops/static/src/scss/design_system.scss",
            "alfa_core_ui_sim_ops/static/src/js/sim_interactions.js",
        ],
    },
    "installable": True,
    "application": False,
}
