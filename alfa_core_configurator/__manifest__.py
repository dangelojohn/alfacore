# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — Configurator Engine",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore",
    "summary": "Eligibility-rule-driven service configurator; signal cascade; 30-day session TTL; benefit audit ledger",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": ["alfa_core_diagnosis", "alfa_fleet"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequences.xml",
        "views/configurator_views.xml",
    ],
    "demo": ["demo/configurator_demo.xml"],
    "installable": True,
}
