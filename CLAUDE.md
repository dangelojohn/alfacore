# CLAUDE.md — AlfaCore Engineering Context

**Read this on every session. It is the durable, version-controlled context for the entire project.**

## What this project is

**AlfaCore** is a luxury automotive service platform for Italian-platform vehicle owners (Alfa Romeo at v1; Fiat / Maserati in v1.1). It is built as an Odoo 19 Enterprise Application — fourteen custom modules in this monorepo, plus the architecture corpus that defines the platform.

The work is customer-facing (vehicle owners interacting via PWA + portal) and operator-facing (advisors, technicians, ownership using Odoo back-office). The Product Configurator is the orchestration spine: customer commits a configuration → orchestrator cascades into sale.order, project.project, project.task, maintenance.request, inspection.report, loaner.allocation, document requests, and communication sequences across nine Odoo modules.

## Source of truth — the architecture corpus

Six documents constitute the architectural authority. Read them in this order on first session, in `docs/architecture/`:

1. **`Alfa-Odoo-Server-Plan-v1.0.md`** — substrate, base modules, Twelve Patterns from ANDREW v2 Part X
2. **`AlfaCore-Service-Plan-v1.0.md`** — customer-facing service model, scanner pipeline, diagnosis engine
3. **`AlfaCore-JTBD-Gap-Analysis-v1.0.md`** — full-lifecycle audit, what Odoo native serves and what it doesn't
4. **`AlfaCore-Configurator-JTBD-Gap-Analysis-v1.0.md`** — Product Configurator audit, eligibility/recommendation architecture
5. **`AlfaCore-Application-Architecture-Blueprint-v1.0.md`** — master architecture, module composition, cascade specification
6. **`AlfaCore-Decision-Log-v1.0.md`** — twenty-four locked decisions; non-negotiable without re-versioning the corpus

If a decision needs to be made that isn't covered in these six documents, **stop and surface it** — do not invent a new architectural decision in code. The Decision Log is binding for v1.0.

## Engineering doctrine — the Twelve Patterns

Every architectural choice in this codebase honors the Twelve Patterns from ANDREW v2 Part X. Internalize these before writing any model or controller:

1. **Finite pipeline stages with observability** — every workflow is a state machine, every transition logged
2. **Auto-detect over config, fail loud** — never default silently; surface mismatches with red badges
3. **Anchor-text extraction (labels = API)** — field labels and API names agree; no translation layer
4. **Per-record isolation** — every record is VIN-scoped or partner-scoped; no cross-customer data smearing
5. **Idempotent timestamped intermediates** — re-running orchestration is a no-op when records already exist
6. **Configuration as data, not code branches** — rules, eligibility, pricing all in data models, never if/else
7. **`canon_label` canonicalization** — DTCs, part numbers, VINs all normalized through a 7-pass canonicalizer
8. **Information budgets per stage** — payload limits at each cascade step; no unbounded growth
9. **Logging as UI** — the user sees the log; opaque background processes are a bug
10. **Honest boundaries** — name the limits explicitly; never assert capability the system doesn't have
11. **Per-record privacy disposition** — `inference_zde` flag on every diagnosis report; PIPEDA auditability
12. **Versioned content** — DTCs, rules, templates all carry revision history; no silent updates

## Module dependency graph

```
alfa_core (application umbrella, base infrastructure)
├── alfa_fleet (customer vehicles)
├── alfa_parts (parts, kits, alternatives)
├── alfa_tsb (TSB corpus, Qdrant-indexed)
├── alfa_service (service orders, quality, bays) — depends on alfa_fleet, alfa_parts
├── alfa_core_scanner (OBD ingestion) — depends on alfa_fleet
├── alfa_core_diagnosis (rule-based triage) — depends on alfa_core_scanner, alfa_tsb, alfa_parts
├── alfa_core_configurator (orchestration engine) — depends on alfa_core_diagnosis, alfa_fleet
├── alfa_core_inspection (digital inspection) — depends on alfa_service
├── alfa_core_loaner (loaner allocation) — depends on alfa_service, native fleet
├── alfa_core_portal (UI surface) — depends on alfa_core_diagnosis, alfa_core_configurator, alfa_core_inspection, alfa_core_loaner
├── alfa_core_app_api (PWA REST API; top of dep tree) — depends on alfa_core_portal
├── alfa_core_campaign (recall outreach) — depends on alfa_core_diagnosis
└── alfa_core_multi_loc (P3 stub for v2)
```

**Custodianship rule:** if a model is defined in module X, *only* module X writes its schema. Module Y may extend module X's model via inheritance — never via parallel definition.

## What is explicitly out of scope

Do not produce these in this codebase. Each has a separate workstream:

- **OWL 2 frontend components** — separate engineering deliverable; this repo is back-end + portal QWeb only
- **DTC content corpus** — ~5000 generic + ~1500 Alfa-specific entries are a curation deliverable, not engineering
- **Triage rule corpus** — rules are authored over time; engine architecture is what we build
- **Hardware engineering** — Vgate iCar Pro BLE 4.0 baseline; OBDLink MX+ for Pro; no PCB, no firmware
- **Marketing site implementation** — Nano Banana / OdooIQ deliverable
- **Payment processor selection** — architecture is processor-agnostic; never hard-code Stripe
- **Stellantis dealer-only integrations** — eAuthority, SDMS, Mopar TechAuthority — gated by dealer status, not in scope
- **3D vehicle rendering / AR / advanced viz** — future R&D
- **Predictive maintenance ML** — insufficient data at v1

If you find yourself reaching for any of these, stop and surface the request.

## Coding conventions

- **Python 3.11+**, Odoo 19 Enterprise patterns
- **LGPL-3** header SPDX identifier on every Python file (`# SPDX-License-Identifier: LGPL-3.0-only`)
- **ruff** for lint and format; **pylint-odoo** for Odoo-specific checks (`pyproject.toml`)
- **Models in `models/`**, one model per file when reasonable, named after the model (`alfa_core_subscription.py` for `alfa_core.subscription`)
- **Views in `views/`**, one XML file per primary record type
- **Security in `security/ir.model.access.csv`** — explicit ACL entries; never omit
- **i18n in `i18n/`** — `en.po`, `fr.po`, `it.po`; translatable strings extracted to all three even if FR/IT remain English at v1
- **Tests in `tests/`** — every new model gets a test; every new workflow gets an integration test
- **Migrations in `migrations/<version>/`** — required for any breaking schema change

## Branching and commits

- **Trunk-based development** — work on short-lived feature branches from `main`
- **Conventional Commits** — `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:` — `semantic-release` reads these to produce version tags
- **One concern per PR** — don't bundle unrelated changes
- **Smoke tests must pass before merge** — Forgejo Actions `lint` and `test` workflows are blocking

## Test and lint commands

```bash
# Lint
ruff check .
ruff format --check .
pylint --rcfile=pyproject.toml alfa_*/

# Format (apply)
ruff format .

# Run smoke tests (requires Odoo install)
odoo-bin -d test_alfacore -i alfa_core_app_api --test-enable --stop-after-init --test-tags=alfacore_smoke

# Sync requirements.txt after manifest changes
python tools/sync_deps.py
```

## What "done" looks like for a feature

A feature is done when all of these are true:

1. Models are defined with proper field types, constraints, and `_check_*` methods
2. Security ACLs are explicit in `ir.model.access.csv`
3. Views render the model in the back-office
4. At least one functional test verifies the workflow
5. Translatable strings are extracted to `i18n/en.po` (FR / IT auto-extract via Odoo i18n tooling)
6. The smoke test for the module still passes
7. `ruff check .` and `ruff format --check .` produce zero output
8. The PR description references the relevant audit section and Decision Log entry

## How to ask for guidance

If you encounter ambiguity that isn't resolved by the corpus or Decision Log:

1. **Surface it explicitly** in the conversation rather than inventing a decision
2. **Reference the relevant audit section** — "JTBD Gap §2.3.3 says X, but the configurator audit §4.2 implies Y"
3. **Propose two or three options** with trade-offs, marked with your recommendation
4. **Do not commit speculative architecture** without confirmation

## Final notes

This codebase is built to last. Honest boundaries (Pattern 10) means we'd rather decline a feature than ship one that overstates the platform's capability. Per-record isolation (Pattern 4) means we'd rather denormalize than smear data across customers. Configuration as data (Pattern 6) means we'd rather author a rule than write an `if` statement.

The architecture earns its complexity by serving real Italian-platform vehicle owners and the technicians who care for their cars. Every model, every view, every test should be evaluable against that purpose.

## Documentation strategy (clarified at scaffold v1.0.1)

Two documentation surfaces, two purposes, kept in sync:

| Surface | Audience | Mechanism |
|---|---|---|
| **`docs/architecture/`** in this repo | Engineering — Claude Code, Aider, human engineers | Git-versioned markdown, source of truth for implementation |
| **AlfaCore Architecture workspace** in Knowledge module | Operations — advisors, technicians, ownership | Populated by `tools/seed_knowledge.py` from `docs/architecture/` |

The repo copy is the engineering canonical. Knowledge is the operational canonical. They are kept in sync — never edit Knowledge directly; edit the markdown in `docs/architecture/` and re-run the seeder.

When you (Claude Code) need to reference architecture, always read from `docs/architecture/`. Never assume Knowledge content is authoritative; the markdown in this repo is.

## Sprint cadence and intentional emptiness

The scaffold ships with intentionally empty:

- `models/` directories (only `__init__.py` placeholder) — first model per module added in its first sprint
- `views/` directories — views added when models exist to view
- `data/` directories — seed data added per module as needed
- `demo/` directories — demo data added inline per module per Decision Log §scaffold-Q4
- `security/ir.model.access.csv` — header only; ACL rows added per model

**Do not pre-populate these directories speculatively.** Each sprint adds what that sprint's models require. Speculative additions accumulate as untested code.

The Sprint kickoff briefs (e.g., `SPRINT-01-KICKOFF.md`) tell you what to add in each cycle.


---

*Last reviewed: 2026-05-11. Update only when the architecture corpus updates.*
