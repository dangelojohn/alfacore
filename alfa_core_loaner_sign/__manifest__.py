# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — Loaner E-Signature (Sign integration)",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore",
    "summary": "Adds Odoo Sign integration to the loaner allocation workflow: send-for-signature, status sync cron, signed-before-pickup gate",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": [
        "alfa_core_loaner",
        "sign",  # Odoo Enterprise — install this sub-module only on EE deployments
    ],
    "data": [
        "data/sign_config.xml",
        "data/cron.xml",
        "views/loaner_allocation_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
