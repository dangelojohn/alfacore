# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — Inspection Workflow",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore",
    "summary": "Multi-point inspections with template reuse, finding-level granularity, customer-approval-gated remediation",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": [
        "alfa_core",
        "alfa_fleet",
        "alfa_service",
        "alfa_parts",
        "hr",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/sequences.xml",
        "views/inspection_views.xml",
    ],
    "demo": [
        "demo/template_demo.xml",
    ],
    "installable": True,
}
