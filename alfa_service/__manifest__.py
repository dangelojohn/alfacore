# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — Service Operations",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore",
    "summary": "Service orders, quality checks, bay allocation, work-order extensions",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": [
        "alfa_fleet",
        "alfa_parts",
        "sale_management",
        "hr",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/service_views.xml",
    ],
    "demo": [
        "demo/bay_demo.xml",
    ],
    "installable": True,
}
