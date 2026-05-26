# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — Loaner Fleet & Allocation",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore",
    "summary": "Shop-owned loaner fleet, allocation workflow, pickup/return condition reports",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": [
        "alfa_core",
        "alfa_fleet",
        "alfa_service",
        "hr",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/sequences.xml",
        "views/loaner_views.xml",
    ],
    "demo": [
        "demo/fleet_demo.xml",
    ],
    "installable": True,
}
