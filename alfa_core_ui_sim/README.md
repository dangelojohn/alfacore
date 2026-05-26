# alfa_core_ui_sim — Umbrella + Journeys

Landing index at `/alfacore/sim` plus four cross-cutting journey surfaces.

## Surfaces

| Slug | Path |
|---|---|
| relationship-tape | `/alfacore/sim/journey/relationship-tape` |
| blueprint-authoring | `/alfacore/sim/journey/blueprint-authoring` |
| configurator | `/alfacore/sim/journey/configurator` |
| safety-critical | `/alfacore/sim/journey/safety-critical` |

## Why it's three modules, not one

`alfa_core_ui_sim_pwa` and `alfa_core_ui_sim_ops` can be installed
independently — useful for a customer-facing demo where you only want the
PWA wireframes installed without the operator-side mockups visible in the
Apps screen.

This umbrella module depends on both of them plus the production modules
needed for live data on the journey surfaces.

## Install order

1. `alfa_core_ui_sim_pwa` (depends only on `alfa_core_app_api`)
2. `alfa_core_ui_sim_ops` (depends on `alfa_core`, `alfa_fleet`, `alfa_service`, `alfa_core_loaner`, `alfa_core_diagnosis`)
3. `alfa_core_ui_sim` (depends on the above + `alfa_core_inspection`, `alfa_core_configurator`, `alfa_core_campaign`)

## Live vs mockup

Every journey surface reads live records by default. Append `?mockup=1`
to any URL for clean design-review visuals. Mock dictionaries are inlined
into the controller methods on this module (the journey surfaces don't
have a shared mockup file the way ops does — each one's mockup payload is
small enough to keep with the live-builder).

The "Live data" / "Mockup data" toggle in the page header makes the swap
visible to stakeholders.

## CI smoke matrix

After installing this trio, append these three names to
`.github/workflows/test.yml` smoke_all matrix entry — see the bottom of
the existing `test.yml` for the existing list.
