# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — Scanner Integration",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore",
    "summary": "OBD-II BLE scanner ingestion: paired devices, scan sessions, DTC + PID capture, offline heartbeat",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": ["alfa_fleet", "alfa_core"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequences.xml",
        "views/scanner_views.xml",
    ],
    "demo": ["demo/scanner_demo.xml"],
    "installable": True,
}
