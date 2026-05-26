# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — Diagnosis Engine",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore",
    "summary": "DTC library, triage rules, diagnosis reports with confidence, Pro-tier review queue",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": ["alfa_core_scanner", "alfa_parts"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequences.xml",
        "data/dtc_data.xml",
        "views/diagnosis_views.xml",
        "views/scan_session_views.xml",
    ],
    "demo": ["demo/diagnosis_demo.xml"],
    "installable": True,
}
