# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — UI Sim · PWA",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore — Internal Tools",
    "summary": "Companion PWA wireframes (4 surfaces) — standalone HTML+JS calling /api/v1/*",
    "description": """
AlfaCore companion-PWA wireframes for stakeholder demos.

Four surfaces served as standalone HTML+JS at /alfa_core_ui_sim_pwa/static/src/pwa/:
- Onboarding
- Digital Garage
- Scan in Progress
- Diagnosis

A server-side controller at /alfacore/sim/pwa issues a short-lived demo JWT
(signed through alfa_core_app_api.jwt_secret_manager — same rotation surface
as production) and redirects to the static index with token=... in the URL
fragment. The static pages read the fragment and fetch /api/v1/* exactly
like the real PWA will.

For internal demo use. Category "Services/AlfaCore - Internal Tools"
groups this alongside the other sim modules in the Apps screen.
""",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": [
        "alfa_core_app_api",
    ],
    "data": [
        "views/error_templates.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": False,
}
