# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — Companion PWA API",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore",
    "summary": "JWT-authenticated /api/v1/* REST endpoints for the AlfaCore companion PWA",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": [
        "alfa_core",
        "alfa_fleet",
        "alfa_core_scanner",
        "alfa_core_diagnosis",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/config.xml",
        "data/cron.xml",
        "views/token_views.xml",
    ],
    "demo": [],
    "external_dependencies": {"python": ["pyjwt"]},
    "installable": True,
}
