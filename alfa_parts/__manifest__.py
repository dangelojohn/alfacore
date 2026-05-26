# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — Parts Master",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore",
    "summary": "OEM SKUs with canonicalization, aftermarket alternatives, service-quote kits, vendor preferences",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": [
        "alfa_core",
        "alfa_fleet",
        "stock",
        "purchase",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/part_views.xml",
    ],
    "demo": [
        "demo/vendor_demo.xml",
        "demo/part_demo.xml",
    ],
    "installable": True,
}
