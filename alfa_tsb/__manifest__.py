# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — TSB Knowledge Surface",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore",
    "summary": "Technical Service Bulletin corpus with Qdrant ingestion plumbing for RAG retrieval",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": [
        "alfa_core",
        "alfa_fleet",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/tsb_views.xml",
    ],
    "demo": [
        "demo/tsb_demo.xml",
    ],
    "external_dependencies": {"python": ["qdrant_client"]},
    "installable": True,
}
