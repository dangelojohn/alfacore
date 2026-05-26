# -*- coding: utf-8 -*-
{
    "name": "AlfaCore — UI Sim · Umbrella & Journeys",
    "version": "19.0.1.0.0",
    "category": "Services/AlfaCore — Internal Tools",
    "summary": "Index landing page + 4 cross-cutting customer-journey wireframes",
    "description": """
Umbrella module for the AlfaCore UI simulation set.

Provides:
- /alfacore/sim — landing page indexing all 12 surfaces by audience
- /alfacore/sim/journey/relationship-tape — customer record / advisor view
- /alfacore/sim/journey/blueprint-authoring — service-blueprint editor
- /alfacore/sim/journey/configurator — configurator cascade flow
- /alfacore/sim/journey/safety-critical — do-not-drive recall handling

Depends on the two audience-split sim modules + production reads from
alfa_core_inspection, alfa_core_configurator, alfa_core_diagnosis,
alfa_core_campaign for live demo context.
""",
    "author": "REAL Partners Ltd. / OdooIQ",
    "website": "https://odooiq.com",
    "license": "LGPL-3",
    "depends": [
        "alfa_core_ui_sim_pwa",
        "alfa_core_ui_sim_ops",
        "alfa_core_inspection",
        "alfa_core_configurator",
        "alfa_core_diagnosis",
        "alfa_core_campaign",
        # `website` provides web.frontend_layout that the umbrella +
        # journey QWeb templates t-call. Without it Odoo crashes on
        # KeyError: 'website' when rendering /alfacore/sim.
        "website",
    ],
    "data": [
        "views/umbrella_templates.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "alfa_core_ui_sim/static/src/scss/design_system.scss",
            "alfa_core_ui_sim/static/src/js/sim_interactions.js",
        ],
        "web.assets_frontend": [
            "alfa_core_ui_sim/static/src/scss/design_system.scss",
            "alfa_core_ui_sim/static/src/js/sim_interactions.js",
        ],
    },
    "installable": True,
    "application": True,
}
