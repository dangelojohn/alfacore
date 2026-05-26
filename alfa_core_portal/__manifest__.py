# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — Customer Portal",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore",
    "summary": "Customer portal pages: vehicles (Digital Garage), diagnoses, inspections with finding approval, loaners",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": [
        "alfa_core",
        "alfa_fleet",
        "alfa_core_diagnosis",
        "alfa_core_inspection",
        "alfa_core_loaner",
        "portal",
        "website",
    ],
    "data": [
        "security/ir_rules.xml",
        "views/portal_templates.xml",
    ],
    "demo": [],
    "installable": True,
}
