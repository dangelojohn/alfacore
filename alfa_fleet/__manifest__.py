# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — Customer Vehicle Master",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore",
    "summary": "Customer-owned vehicle records, VIN-keyed, platform/engine/trim, per-vehicle preferences",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": [
        "alfa_core",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/platform_data.xml",
        "data/engine_data.xml",
        "data/trim_data.xml",
        "views/platform_views.xml",
        "views/engine_views.xml",
        "views/vehicle_views.xml",
        "views/menus.xml",
    ],
    "demo": [
        "demo/vehicle_demo.xml",
    ],
    "installable": True,
    "external_dependencies": {"python": ["requests"]},
}
