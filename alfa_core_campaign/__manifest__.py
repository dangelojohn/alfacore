# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — Recall Campaigns",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore",
    "summary": "NHTSA recall ingestion, per-vehicle targeting, customer notification dispatch",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": [
        "alfa_core",
        "alfa_fleet",
        "sale_management",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/cron.xml",
        "views/campaign_views.xml",
    ],
    "demo": [
        "demo/campaign_demo.xml",
    ],
    "installable": True,
}
