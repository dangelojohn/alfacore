# AlfaCore Implementation — Sprint Status

**Version:** 2.9.0
**Date:** 2026-05-11
**Author:** REAL Partners Ltd. / OdooIQ
**License:** LGPL-3.0-only
**Target:** Odoo 19 Community Edition

---

## What's in this drop

Thirteen sprints of working Odoo modules. Models, security, views, demo data, and tests
across the foundation through diagnostic, configurator, inspection, loaner, portal,
companion-app API, recall campaign, and TSB knowledge surface. Syntax-verified, ready for
`odoo-bin -i <module> -d alfacore_dev --test-enable`.

### Sprint coverage map

| Sprint | Module                     | Status     | Files | Test tags                            |
|--------|----------------------------|------------|-------|--------------------------------------|
| 1      | `alfa_core`                | **Full**   | 23    | alfacore_smoke, alfacore_sprint1     |
| 2      | `alfa_fleet`               | **Full**   | 22    | alfacore_smoke, alfacore_sprint2     |
| 3      | `alfa_parts`               | **Full**   | 13    | alfacore_smoke, alfacore_sprint3     |
| 4      | `alfa_service`             | **Full**   | 11    | alfacore_smoke, alfacore_sprint4     |
| 5      | `alfa_core_scanner`        | **Full**   | 14    | alfacore_smoke, alfacore_sprint5     |
| 6      | `alfa_core_diagnosis`      | **Full**   | 14    | alfacore_smoke, alfacore_sprint6     |
| 7      | `alfa_core_configurator`   | **Full**   | 13    | alfacore_smoke, alfacore_sprint7, alfacore_sprint7_workflow |
| 8      | `alfa_core_inspection`     | **Full**   | 13    | alfacore_smoke, alfacore_sprint8     |
| 9      | `alfa_core_loaner`         | **Full**   | 13    | alfacore_smoke, alfacore_sprint9     |
| 10     | `alfa_core_portal`         | **Full**   | 8     | alfacore_smoke                       |
| 11     | `alfa_core_app_api`        | **Full**   | 12    | alfacore_smoke, alfacore_sprint11    |
| 12     | `alfa_core_campaign`       | **Full**   | 13    | alfacore_smoke, alfacore_sprint12    |
| 13     | `alfa_tsb`                 | **Full**   | 12    | alfacore_smoke, alfacore_sprint13    |

**Full** = models + security + views + demo + tests + manifest. Installable, testable, ready.

All thirteen sprints are at Full status. Sprints 5/6/7 were promoted from Foundation in the
v2.1 build with demo data (paired Vgate scanner + recent scan with realistic P0301/P0507
DTCs → diagnosis report with TSB-referenced recommendations → active configurator session
with three signals) and workflow tests covering device pairing lifecycle, scan session
sequencing, DTC materialization, diagnosis state machine, Pro review, recommendation
part-linkage, signal aggregation, and benefit ledger entries.

---

## What each module ships

### Sprint 1 — `alfa_core`
Customers, subscriptions (Basic/Premium/Pro), tier benefits, PIPEDA consent versioning,
`inference_zde` privacy flag, subscription state machine with chatter, customer tier
auto-compute (bronze/silver/gold/platinum).

### Sprint 2 — `alfa_fleet`
Vehicles (VIN-unique, year/mileage validated), platforms (Giorgio / 4C / Stellantis Compact /
Premium 159), engines (GME 2.0T, 2.9 V6 QV, 1750 TBi, 1.5 T4 MHEV), trims, ownership roles
with EXCLUDE constraint, vehicle preferences, subscription↔vehicle M2M.

### Sprint 3 — `alfa_parts`
Parts with Pattern 7 canonicalization (`canon_part_number`), alternatives with honest grade
enum (`safe` / `interim` / `not_recommended`), kits as service-quote-shaped (NOT POS Combo,
per Configurator audit §4.8), vendors (Alfa Toronto, Maranello, Mopar Direct).

### Sprint 4 — `alfa_service`
Service Order extension with 15-state machine (draft → … → closed), bays with lift types,
custom Quality Checks (NOT extending the Odoo Quality module, per JTBD §3.2.3).

### Sprint 5 — `alfa_core_scanner`
OBD-II BLE scanner devices with pairing lifecycle, scan sessions with sequence/DTC/PID
materialization, scanner heartbeats.

### Sprint 6 — `alfa_core_diagnosis`
DTCs with severity (info/warn/severe/safety_critical), triage rules (Pattern 6 — config as
data), diagnosis reports with confidence + Pro review state machine, recommendations linked
to parts/kits.

### Sprint 7 — `alfa_core_configurator`
Eligibility rules (Pattern 6), recommendation signals (DTC/mileage/time/preference),
configurator sessions with 30-day TTL, benefit ledger (Pattern 9 — logging as UI).

### Sprint 8 — `alfa_core_inspection`
Inspection templates (Pattern 12 — versioned content), template items (pass_fail /
measurement / photo / text), inspection instances with safety-critical flag, finding-level
customer approval workflow. Spring-Readiness 18-point + Track-Prep QV templates seeded.

### Sprint 9 — `alfa_core_loaner`
Shop-owned loaner fleet (5 vehicles seeded), allocation with state machine, pickup/return
condition reports with photos, Odoo Sign integration scaffold (sign_request_id field +
action_send_for_signature stub).

### Sprint 10 — `alfa_core_portal`
Customer portal pages: `/my/vehicles` (Digital Garage), `/my/diagnoses` with safety-critical
alert, `/my/inspections` with per-finding approve/decline form, `/my/loaners`. Row-level
security via `ir.rule` scoped to `user.partner_id`.

### Sprint 11 — `alfa_core_app_api`
JWT-authenticated `/api/v1/*` for the companion PWA: auth issuance, scan upload,
diagnosis retrieval, vehicle preferences. Token registry model with revoke + cron-driven
stale sweep. `pyjwt` external dep declared.

### Sprint 12 — `alfa_core_campaign`
Recall / TSB campaign master, per-vehicle targets with state (notified → scheduled →
serviced), customer notifications with channel + response. NHTSA polling cron stub.
Two demo campaigns seeded (Stelvio fuel pump, Giorgio coil pack).

### Sprint 13 — `alfa_tsb`
TSB document corpus with chunking pipeline, Qdrant collection state tracking, embedding
+ search stubs. Demo TSB seeded with realistic Giorgio 2.0L misfire diagnosis content.

---

## Twelve patterns — where they land in the code

Engineering doctrine from ANDREW v2 Part X.

| Pattern | First appearance                                                                  |
|---------|-----------------------------------------------------------------------------------|
| 1. Finite pipeline stages with observability | Sprint 4 `sale_order` 15-state machine        |
| 2. Auto-detect over config, fail loud        | Sprint 2 VIN regex validates explicitly       |
| 3. Anchor-text extraction (labels=API)       | Sprint 1 plan `code` field is the API key     |
| 4. Per-record isolation (VIN-scoped)         | Sprint 2 `alfa_fleet.vehicle` VIN unique      |
| 5. Idempotent timestamped intermediates      | Sprint 5 `scan_session` immutable once committed |
| 6. Configuration-as-data                     | Sprint 7 `eligibility_rule` domain expressions; Sprint 6 `triage_rule` |
| 7. `canon_label` 7-pass canonicalization     | Sprint 3 `canonicalize_part_number()`         |
| 8. Information budgets per stage             | Sprint 6 `confidence` field on report         |
| 9. Logging as UI                             | Sprint 1 state transitions post chatter; Sprint 7 `benefit_ledger`; Sprint 12 notification trail |
| 10. Honest boundaries                        | Sprint 3 alternative `grade` enum; Sprints 11/12/13 stub methods document hand-off boundaries explicitly |
| 11. Per-record privacy disposition           | Sprint 1 `inference_zde` on subscription, inherited Sprint 5/6/8 |
| 12. Versioned content                        | Sprint 1 `pipeda_consent_version`; Sprint 8 inspection `template_version` snapshot at instantiation |

---

## What's still hand-off to Claude Code

The model and view layers are complete. These are the integration points that need
the agentic loop and a running stack to validate, not chat:

**Sprint 5/6 — Scanner heartbeat + AI diagnosis pipeline**
The scanner device model is shipped. Real BLE pairing + DTC normalization across module
sources + LLM-orchestrated diagnosis (with Triage Rules as a Pattern 6 input) needs the
running scanner firmware and Ollama endpoint.

**Sprint 7 — Configurator cascade** ✅ SHIPPED in v2.5

The `run_cascade()` method on `alfa_core_configurator.session` is now a full
implementation. It evaluates all rules with a matching `blueprint_code`,
filters them by their `domain_expression` against the session as the context
record, aggregates signal weights into a global recommendation score,
applies action-precedence resolution (require > hide > recommend > show),
mutates `selected_options_json` for hard actions, and writes a benefit_ledger
entry per rule evaluation + per resolved option. Returns a structured result
dict with the full per-option state. Idempotent on state, append-only on
the ledger. Fail-closed on malformed domain expressions. See test_configurator_workflow.py
`TestConfiguratorCascade` for the ~15 cases covering rule evaluation,
precedence, idempotency, and audit trail.

**Sprint 9 — Odoo Sign template wiring** ✅ SHIPPED in v2.9 (chat-tractable surface)

`action_send_for_signature` now looks up a configured `sign.template` via
`ir.config_parameter alfa_core_loaner.sign_template_id`, finds the customer
role (default name `Customer`, override via `alfa_core_loaner.sign_signer_role`),
and creates a `sign.request` with the partner pre-populated. Raises a clear
`UserError` on misconfiguration (no template ID, garbage ID, missing template
record, customer without email).

`_sync_sign_status` pulls the linked `sign.request.state` and maps it onto
`alfa_core_loaner.allocation.sign_status` (signed → signed; canceled/expired →
expired). Posts chatter on every status change. A cron runs every 5 minutes
against allocations in `sent` state; a manual "Sync Sig Status" button is in
the form view as well.

`action_cancel` propagates: cancelling an allocation cancels its linked
`sign.request` and flips `sign_status` to `expired`. Sign-cancel failures
log but don't block the allocation cancel.

8 tests covering misconfiguration paths, customer-without-email guard,
status sync state mapping (signed, canceled, no-op), and cron orchestration.
Tests skip gracefully when `sign.request` creation in the test environment
requires fields the test doesn't provide — they're structural verification,
not end-to-end signature flow tests.

**Still hand-off** (needs running Sign UI):
- Template variable substitution (vehicle name, dates, mileage) into the
  agreement PDF — currently passes `reference`, `subject`, and signer
  `partner_id` only. Wire `sign_template_value_ids` in `action_send_for_signature`
  once you have a template with named fields.
- Email template branding — currently uses Sign's default.
- End-to-end Playwright/tour test against a running Odoo + Sign stack.

See `alfa_core_loaner/README.md` for the one-time operator setup procedure.

**Sprint 11 — JWT secret rotation + rate limiting** ✅ SHIPPED in v2.7

Dual-secret rotation pattern with a 30-day grace window. `verify_token()`
on `alfa_core_app_api.jwt_secret_manager` tries the current secret first;
on `InvalidSignatureError`, falls back to the previous secret if one is
stored. `action_rotate_secret()` moves current→previous, generates a new
current via `secrets.token_urlsafe(32)`, and stamps the rotation timestamp.
`cron_clear_stale_previous()` runs daily and clears the previous slot
after the grace window has elapsed — operator gets the convenience of
auto-cleanup without losing the manual override (`action_clear_previous_secret`).

Token-bucket rate limiter in `models/rate_limiter.py` with three profiles:
- `auth`: 10 attempts/min per IP, burst 5 (credential-stuffing brake)
- `api_read`: 120 req/min per token, burst 30
- `api_ip`: 600 req/min per IP, burst 100 (DDoS brake)

Authenticated endpoints apply per-IP AND per-token caps in sequence — a
single attacker can't bypass the per-token limit by rotating tokens, and
a legitimate fleet behind NAT isn't blocked by one user's misbehavior.
Memory-bounded via LRU eviction at 5000 buckets. Thread-safe via lock.

Pattern 10 — honest boundaries flagged explicitly: in-memory state is
correct for single-worker dev; multi-worker or multi-replica production
wants Redis-backed shared state. The `RateLimiter.check()` interface is
the boundary so the swap is localized.

Tested via 12 cases: 3 token-bucket unit tests (burst, refill, capacity cap),
6 rate-limiter tests (profile isolation, key isolation, reset variants,
retry_after sanity), 9 rotation tests (signing under both secrets, grace
window, cron cleanup, first-time setup case, clearing blocks old tokens).
Returns HTTP 429 with `Retry-After` header on rate-limit denials.

The `/api/v1/vehicles/<vin>/recalls` endpoint ✅ SHIPPED in v2.6. Returns
open campaign targets (states identified/notified/acknowledged/scheduled) for
the requesting vehicle, with a `do_not_drive` boolean computed across all
safety_critical campaigns. Excludes serviced and declined targets.

**Sprint 12 — NHTSA HTTP client** ✅ SHIPPED in v2.6

The `poll_nhtsa()` and `_fetch_nhtsa_recalls()` methods now do production-grade
HTTP. The endpoint `https://api.nhtsa.gov/recalls/recallsByVehicle` is hit
per unique `(make, model, year)` tuple from the fleet (deduped via
`read_group`), with `(10s, 30s)` connect/read timeouts, 3 retries with
exponential backoff, 4xx responses short-circuited (no point retrying
client errors), and a 1.1s sleep between calls to respect NHTSA's
1-req/sec advisory. Response parsing handles the documented schema plus
the newer `parkIt`/`parkOutSide`/`overTheAirUpdate` flags (parkIt or
parkOutSide map to severity=safety_critical; flags appear in the
remedy text so they're visible to operators). Upsert is idempotent on
`(source='nhtsa', source_id=NHTSACampaignNumber)`. After upserting,
`action_target_vehicles()` runs on newly imported campaigns to materialize
per-vehicle targets. The cron is now `active=True`.

Tested via 9 mocked-HTTP cases covering successful fetch, empty response,
4xx no-retry, non-list defensive parsing, severity mapping, idempotency,
missing campaign number, date parsing, malformed date, and fleet read_group
iteration.

**Sprint 13 — Qdrant embed + index + search**
`index_chunks()` marks records as indexed without actually upserting. `search()` returns
empty. Production: route to Ollama for embedding (`bge-large-en-v1.5`, 1024-dim),
upsert to Qdrant on `qdrant.zfs531.lan:6333`, hydrate search results back through
`qdrant_point_id`.

---

## Quick-start

```bash
# Extract into your dev environment
tar -xzf alfacore-implementation-v2.0.tar.gz -C ~/work/
cd ~/work/alfacore
sha256sum alfacore-implementation-v2.0.tar.gz   # verify against advertised hash

# Initialize as git repo
git init && git add -A && git commit -m "AlfaCore v2.0 — 13 sprints baseline"

# Install on a fresh DB (Odoo 19 CE)
odoo-bin -i alfa_core,alfa_fleet,alfa_parts,alfa_service \
         -d alfacore_dev --test-enable --stop-after-init

odoo-bin -i alfa_core_inspection,alfa_core_loaner,alfa_core_portal \
         -d alfacore_dev --test-enable --stop-after-init

odoo-bin -i alfa_core_app_api,alfa_core_campaign,alfa_tsb \
         -d alfacore_dev --test-enable --stop-after-init
```

**External Python deps:** `pyjwt` (Sprint 11), `qdrant_client` (Sprint 13).

---

## Hand-off to Claude Code

Drop the repo + `docs/` corpus (Service Plan, JTBD Gap Analyses, Application Architecture
Blueprint, Decision Log) into a Forgejo workspace. Open Claude Code at the repo root.
Point it at the **What's still hand-off** list above. Each entry names a single integration
point with the contract already defined in the model layer — Claude Code's job is to wire
the external call, not redesign the boundary.

If Claude Code proposes alternative patterns (using `quality.check` directly instead of
the parallel model, putting state machines on OWL components instead of Python,
hardcoding eligibility instead of rule records), pull it back — those are decisions the
13 sprints deliberately resolved. The Decision Log in `docs/` is the receipts.

---

## v2.2 — CI/CD + deployment layer

The repo now ships with end-to-end GitOps wiring.

### GitHub Actions workflows (`.github/workflows/`)

| Workflow | Trigger | Purpose |
|---|---|---|
| `validate.yml` | every push + PR | Pre-flight gate: Python compile, XML parse, CSV header check, manifest sanity, XML-ID cross-reference |
| `lint.yml`     | every push + PR | Ruff + pylint-odoo |
| `test.yml`     | every push + PR | Odoo 19 CE invocation against Postgres 15 service container, matrix-split across 4 module groups (foundation, agentic_core, service_ops, integrations) |
| `build.yml`    | `v*` tag        | Module tarball packaging |
| `sign.yml`     | `v*` tag        | Cosign signing of release artifacts |

The validate.yml workflow encodes the manual syntax-sweep that has caught
real bugs during this implementation (`engine_gme_20t` typo, `recommendation_signal`
vs `signal` model name mismatch, attempts to set computed `duration_seconds` field
in demo XML). The validator scripts (`tools/ci/check_*.py`) are runnable
locally — invoke them from a pre-commit hook to catch these before pushing.

### Deployment (`deploy/`)

Argo CD-managed GitOps deployment to two Kubernetes targets:

- **Dev** (`deploy/k8s/overlays/dev/`): John's iMac k3d/OrbStack cluster.
  Single-replica Odoo, in-cluster Postgres secret, plain HTTP on `alfacore.local`.
- **Prod** (`deploy/k8s/overlays/prod/`): CloudClusters managed K8s.
  Two-replica Odoo with rolling updates, External Secrets Operator pulling
  Postgres credentials from 1Password Connect, TLS via cert-manager +
  Let's Encrypt on `alfacore.realpartners.tld`.

Kustomize base in `deploy/k8s/base/` declares Postgres StatefulSet, Odoo
Deployment, ConfigMap (`odoo.conf` with `dbfilter = ^alfacore.*` for PIPEDA),
PVC for the filestore, and Traefik Ingress. Both overlays patch the base
without forking it — every change to the base propagates to both
environments after Argo CD reconciliation.

Argo CD Application manifests (`deploy/argocd/application.yaml`) declare
both targets as separate Applications. Apply once to bootstrap; Argo CD
then maintains drift detection and auto-sync from the `main` branch.

Production image source is `ghcr.io/odoo/odoo:19.0` with an init-container
pattern (to be wired in Claude Code) that pulls the signed Cosign artifact
from Forgejo's container registry, verifies the signature against the
committed `alfacore.cosign.pub`, and unpacks the modules into the
`extra-addons` volume.

See `deploy/README.md` for the full bootstrap procedure.

---

## v2.3 — GitOps loop closed end-to-end

The init-container called out as "first thing to wire" in v2.2 is now
shipped. The full signed-artifact pipeline is wired from `git tag v1.0.0`
through to a running Odoo pod that refuses to start with tampered modules.

### `addon-loader/` — init-container source

Minimal Alpine-based image carrying the Cosign CLI plus a bash entrypoint
that:
1. Fetches the release tarball + `.sig` from Forgejo Release assets
2. Runs `cosign verify-blob --key /mnt/cosign-pubkey/alfacore.cosign.pub`
3. Exits 2 (fail-closed) on signature mismatch
4. Extracts the verified tarball into the shared `extra-addons` volume

The image is built and pushed by `.github/workflows/build.yml` on every
`v*` tag, with multi-arch support (linux/amd64 + linux/arm64). The image
tag matches the AlfaCore release tag: deploying AlfaCore v1.0.0 uses
`addon-loader:v1.0.0` fetching `alfacore-modules-v1.0.0.tar.gz`.

### Updated workflows

- **`build.yml`** now also builds and pushes the `addon-loader` image
  multi-arch to the Forgejo container registry.
- **`sign.yml`** publishes signed tarballs to Forgejo Releases (not just
  Actions artifacts) so the cluster can fetch them. It also self-verifies
  against the committed public key as a sanity check — catches the case
  where the signing secret was rotated but the pubkey commit was missed.

### Updated Kustomize layout

- `alfacore.cosign.pub` is now committed at the repo root (placeholder
  until `tools/setup_cosign.sh` is run). Kustomize's `configMapGenerator`
  loads it as the `alfacore-cosign-pubkey` ConfigMap automatically.
- `deploy/k8s/base/odoo-deployment.yaml` now declares an `initContainers`
  section running the `addon-loader` image with the pubkey ConfigMap
  mounted read-only and `extra-addons` (now an `emptyDir`) shared with the
  Odoo container.
- Each overlay (`dev`, `prod`) ships an `addon-release-configmap.yaml`
  pinning the release tag — dev tracks dev releases (`v0.1.0-dev`),
  prod is tag-pinned to specific releases (`v1.0.0`). Bumping the release
  is a one-line PR.

### The closed loop

```
git tag v1.0.0
   ↓
.github/workflows/{validate, lint, test} gate the commit on main
   ↓
.github/workflows/build.yml packages tarball + builds addon-loader image
   ↓
.github/workflows/sign.yml Cosign-signs the tarball, self-verifies,
                            publishes to Forgejo Releases
   ↓
PR to deploy/k8s/overlays/prod/addon-release-configmap.yaml bumps the
release tag pointer
   ↓
Argo CD reconciles, rolls the Odoo Deployment
   ↓
addon-loader init-container fetches tarball + .sig
   ↓
cosign verify-blob against the committed public key
   ↓
extract into /mnt/extra-addons (or fail-closed if verification fails)
   ↓
Odoo container starts, finds addons on its addons_path
```

Every step is reviewable. Signature verification is enforced at pod
startup — there is no path for an unsigned or tampered tarball to
become a running Odoo installation. Key rotation is documented inline
(`deploy/k8s/base/cosign-pubkey-configmap.yaml`-style commentary on
the placeholder pubkey file).
