# AlfaCore — Sprint Progress

**Status as of 2026-05-11 · Implementation v1.0**

This document tracks engineering progress against the 13-sprint plan defined in
the Application Architecture Blueprint v1.0. It is the canonical "what's
shipped" reference for Claude Code, future engineers, and the technical CTO.

---

## ✅ Sprint 1 — `alfa_core` (foundation) — COMPLETE

**Goal:** Provide the AlfaCore application root, partner extensions, PIPEDA
consent infrastructure, subscription model, security groups, and top-level
menus.

### Models shipped
- `res.partner` extended with: `alfa_core_customer`, `alfa_core_signup_date`,
  `alfa_core_pipeda_consent_*` (group-scoped), `alfa_core_preferred_channel`,
  `alfa_core_tenure_years` (computed/stored), `alfa_core_lifetime_spend`
  (computed/stored), `alfa_core_customer_tier` (computed/stored Bronze→Platinum),
  `alfa_core_subscription_ids`, `alfa_core_active_subscription_id`
- `alfa_core.subscription.plan` — Basic / Premium / Pro, CAD pricing, ZDE default
- `alfa_core.tier.benefit` — structured benefit rows per Configurator audit §2.1.3
- `alfa_core.subscription` — state machine (trial→active→past_due→cancelled|expired)
  with chatter logging on every transition, ZDE inheritance from plan

### Security
- Module category + 4 groups (User, Advisor, Manager, PIPEDA Officer)
- 2 record rules (portal-own + advisor-all on subscriptions)
- 12 ACL rows across 3 models

### Views
- Subscription plan list/form/kanban with handle, badges, benefit inline editor
- Subscription list/form/kanban with state decorations, action buttons gated by state
- Tier benefit inline editable list
- Partner form extended with AlfaCore tab + group-scoped PIPEDA section
- Top-level menu with Customers / Subscriptions / Configuration submenus

### Data
- `ir.sequence` for `AC-SUB-YYYY-NNNNN` format
- Daily `ir.cron` to refresh customer metrics
- `ir.config_parameter` for PIPEDA consent version (`2026-05`)

### Demo data
- 3 subscription plans (Basic $9 / Premium $24 / Pro $59 CAD monthly)
- 14 benefit rows across the 3 plans
- 3 demo partners (D'Angelo 1280d tenure, Bianchi 420d, Rossi 60d trial)
- 3 demo subscriptions (active/active/trial) — Premium / Pro / Basic

### Tests (26 tests, all tagged `alfacore_sprint1`)
- `test_install` — 2 install smoke tests
- `test_partner_extensions` — 9 tests covering signup stamp, tier compute scenarios
  (bronze/silver/gold), PIPEDA officer access gating
- `test_subscription_lifecycle` — 11 tests covering auto-naming, ZDE inheritance,
  all valid state transitions, all invalid transition rejections, chatter writes
- `test_demo_data` — 6 tests verifying demo plans load with correct pricing

### Run the tests
```bash
odoo --test-tags=alfacore_sprint1 -i alfa_core --stop-after-init
```

---

## ✅ Sprint 2 — `alfa_fleet` (vehicle master) — COMPLETE

**Goal:** VIN-keyed customer vehicle records, platform/engine/trim taxonomy,
ownership through-model with role enforcement, per-vehicle preferences.

### Models shipped
- `alfa_fleet.platform` — Giorgio, 4C, Pre-2017 Alfa
- `alfa_fleet.engine` — 5 engine variants seeded (GME 2.0T 280HP, GME 2.0T 252HP,
  2.9 V6 QV, 1750 TBi, 1.4 TB MultiAir) with full specs including oil capacity,
  OEM oil spec, default viscosity
- `alfa_fleet.trim` — 4 trims seeded (Stelvio Ti, Stelvio QV, Giulia QV, 4C Spider)
  with M2M to typical engines and `is_track_eligible` flag
- `alfa_fleet.vehicle` — **the central VIN-keyed record**
  - 17-char VIN with regex constraint excluding I/O/Q
  - VIN canonicalization in `create`/`write` hooks (Pattern 7)
  - Computed `display_name` ("2018 Stelvio Ti · ZASFAKBN3J7C12345")
  - State machine (active/inactive/sold/totaled)
  - `mail.thread` for tracking changes
- `alfa_fleet.vehicle.ownership` — through-model
  - 4 roles (primary_driver, secondary_driver, account_holder, authorized_caller)
  - SQL uniqueness on (vehicle, partner, role)
  - `_check_one_primary_driver` constraint
- `alfa_fleet.vehicle.preference` — fluid specs, tire prefs, alignment specs,
  11 categories
- `res.partner` extended with `alfa_fleet_ownership_ids` + vehicle_count
- `alfa_core.subscription` extended with `vehicle_ids` M2M
  **(closes Sprint 1 TODO)**

### Security
- 1 record rule (portal own-vehicles only)
- 24 ACL rows across 6 models

### Views
- Vehicle list (with decoration-muted for sold/totaled), form (with notebook for
  Ownership/Preferences/Notes), search (filters + group by platform/engine/year)
- Platform / Engine / Trim list+form
- Fleet menu under AlfaCore root with Taxonomy submenu (manager-only)

### Data
- 3 platforms seeded
- 5 engine variants with full specs

### Demo data
- 4 trims (Stelvio Ti, Stelvio QV, Giulia QV, 4C Spider)
- 2 demo vehicles:
  - D'Angelo 2018 Stelvio Ti (VIN ZASFAKBN3J7C12345, 89,247 km, GME 2.0T 252)
  - Bianchi 2020 Giulia Quadrifoglio (VIN ZARFAEBN8L7654321, 42,180 km, 2.9 V6)
- Ownership records (both primary_driver)
- 2 service preferences on D'Angelo's Stelvio (Selenia 5W-40, Pirelli P-Zero)
- Subscription→vehicle links written

### Tests (9 tests, all tagged `alfacore_sprint2`)
- `test_vehicle` — 6 tests covering VIN canonicalization (uppercase, separator
  strip, length validation, character validation, duplicate rejection, display
  name format)
- `test_ownership` — 3 tests covering primary driver uniqueness, computed
  primary_owner_id, secondary driver does not set primary

### Run the tests
```bash
odoo --test-tags=alfacore_sprint2 -i alfa_fleet --stop-after-init
```

---

## 🚧 Sprint 3 — `alfa_parts` (partial sketch from prior session)

**Status:** Pre-existing scaffolding from a prior session, not yet completed in
this implementation pass. Models referenced include `alfa_parts.part`,
`alfa_parts.part.vendor`, kit composition. Will be completed when Sprint 3 is
formally opened.

---

## ⏳ Sprints 4-13 — Pending

The architecture corpus and decision log fully define these. They are
**not yet implemented** in this code package.

| Sprint | Module | Scope | Status |
|--------|--------|-------|--------|
| 4 | `alfa_service` | Sale order extensions, ServiceBay, QualityCheck (custom), state machine | Pending |
| 5 | `alfa_core_scanner` | Device, ScanSession, ScanDTC, ScanPID, ScannerHeartbeat | Pending |
| 6 | `alfa_core_diagnosis` | DTC library, TriageRule, DiagnosisReport, DiagnosisRecommendation | Pending |
| 7 | `alfa_core_configurator` | EligibilityRule, BenefitLedger, ConfiguratorSession, orchestrator cascade | Pending |
| 8 | `alfa_core_inspection` | InspectionPoint, InspectionTemplate, InspectionReport (P0) | Pending |
| 9 | `alfa_core_loaner` | LoanerVehicle, LoanerAllocation, agreement signing | Pending |
| 10 | `alfa_core_portal` | QWeb portal templates, advisor cockpit, technician tablet | Pending |
| 11 | `alfa_core_app_api` | JWT controllers for mobile PWA + API consumers | Pending |
| 12 | `alfa_core_campaign` | RecallCampaign with VIN-range filter, NHTSA integration | Pending |
| 13 | `alfa_tsb` | TSBBulletin with Qdrant integration | Pending |

---

## ✅ Sprint 14 — `alfa_core_cuore` (CUORE bundle import, Foundation) — INSTALLED LIVE 2026-10-22

**Goal:** Offline, file-based import of CUORE diagnostic bundles (`*.cuore.zip`, schema
`cuore.bundle/1.0`) into scan sessions, diagnosis reports and inspection steps. No network link, no tokens.

- Models: `alfa.cuore.bundle`, import wizard `alfa.cuore.import.wizard`, vendored `lib/bundle_schema.py`.
- Idempotent re-import via uuid5 ids; imported readings are read-only.
- Branch `feature/alfa_core_cuore`: `1f7ac55` (feature) + `452c10d` (`.po` fix), merged to `main` as `a7dce7b`.
- Tested on a throwaway database (3 Odoo tests pass), then **installed on the live `alfacore` database on
  2026-10-22** after a pre-install backup. Record: `docs/deployment/OdooIQ-QNAP-2026-10-22.md`.
- Still open: pilot with one real service order by file; deferred items are listed in `alfa_core_cuore/README.md`.

---

## Installation order

To bring up the demo environment from a clean Odoo 19 install:

```bash
# 1. Install alfa_core (provides groups + categories that alfa_fleet depends on)
odoo -i alfa_core -d alfacore_pilot --without-demo=False

# 2. Install alfa_fleet
odoo -i alfa_fleet -d alfacore_pilot

# 3. Run the test suites
odoo --test-tags=alfacore_sprint1,alfacore_sprint2 -d alfacore_pilot --stop-after-init
```

Expected counts on a clean install: 35 tests pass · 3 subscription plans loaded ·
2 demo vehicles · 3 demo customers · 1 active D'Angelo Premium subscription
linked to the Stelvio.

---

## What this implementation pass deliberately did NOT do

- **No DTC content** — codes like P0301, C0561 are illustrative only. The DTC
  library is a content workstream and arrives with Sprint 6.
- **No triage rules** — rule corpus arrives with Sprint 6.
- **No OWL components** — the UI simulation widgets are visual reference targets,
  not React/OWL source. Frontend implementation is a separate phase.
- **No scanner hardware drivers** — the mobile PWA + Bluetooth pairing is a
  separate codebase (React Native or PWA) outside this Odoo monorepo.
- **No NHTSA / Qdrant integrations** — Sprint 12 and 13 respectively.
- **No JWT API** — Sprint 11.

The Twelve Patterns are observed throughout the existing code (per-record
isolation via VIN, canonicalization at write boundaries, honest boundaries on
state transitions, logging-as-UI via chatter + structured logger, finite stages
with observability).
