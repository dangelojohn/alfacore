# alfa_core_ui_sim_pwa

Companion-PWA wireframes for stakeholder demos. Four surfaces served as
standalone HTML+JS — the PWA chrome is intentionally distinct from Odoo's
back-office chrome, because the real PWA is a separate app.

## Surfaces

| Slug | Path |
|---|---|
| onboarding | `/alfacore/sim/pwa/onboarding` |
| digital-garage | `/alfacore/sim/pwa/digital-garage` |
| scan-in-progress | `/alfacore/sim/pwa/scan-in-progress` |
| diagnosis | `/alfacore/sim/pwa/diagnosis` |

## How it works

1. Operator hits `/alfacore/sim/pwa/<surface>` while logged in to Odoo (`auth='user'`).
2. The Python controller (`controllers/pwa_launch.py`) mints a short-lived
   demo JWT (5-minute TTL) for `alfa_core.partner_dangelo` via
   `alfa_core_app_api.jwt_secret_manager` — same rotation surface as production.
3. The controller redirects to the static HTML page with the token in the
   **URL fragment** (`#token=<jwt>`).
4. The static page's JS reads `window.location.hash`, strips the token, and
   uses it as `Authorization: Bearer <jwt>` against `/api/v1/*`.

URL fragment instead of cookie/query: fragments don't get sent server-side
on subsequent fetches, so the bearer doesn't end up in access logs.

## Mockup mode

Append `?mockup=1` to any surface URL. The controller skips JWT issuance,
the static page skips the `/api/v1/*` fetches and uses bundled `MOCKUP_DATA`.
The watermark in the corner changes from `WIREFRAME · LIVE DATA` to
`WIREFRAME · MOCKUP`.

Use for design-review sessions where you want clean visuals without "wait,
is the recall count right?" distractions.

## Phase-2 placeholders

The Diagnosis surface includes a dashed-border placeholder card labeled
"Phase 2 · AI narrative" with the `future capability` badge. v1.0 ships
rule-based diagnosis output only (DTC + triage rule + recommended action);
AI-generated prose narratives are explicitly out of scope per Pattern 10
(honest boundaries) in the architecture corpus.

## Static asset bundling

These pages live under `static/src/pwa/` and are served raw by Odoo —
**outside** the SCSS asset pipeline. The CSS at
`static/src/css/design_system.css` is a hand-mirror of the umbrella
module's SCSS. Keep them in sync.

## Tests

```bash
make test-local MODULE=alfa_core_ui_sim_pwa
```

Smoke tests verify install + static file presence + launch controller
redirect behavior. Functional verification of the JS surface needs a
browser; we don't run that in CI.
