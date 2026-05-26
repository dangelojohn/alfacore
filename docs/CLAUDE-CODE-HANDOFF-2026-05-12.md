# Claude Code → Claude.ai Handoff — AlfaCore platform

**Snapshot date:** 2026-05-12
**Repo HEAD when authored:** `73a48d0` (loaner split + Alfa Romeo logo icons)
**Author of this document:** Claude Code (Anthropic Claude Opus 4.7, 1M ctx) running in `naadmin`'s shell
**Purpose:** describe everything Claude Code did to / created for / installed on the AlfaCore Odoo platform during the 2026-05-11 → 2026-05-12 work session, so Claude.ai can update its mental model of the co-programmed project.

This is a **point-in-time snapshot**. Anything documented here may have shifted by the time you read it — `git log` and the QNAP runtime are authoritative.

---

## 0. TL;DR — what changed

- **Repo moved to GitHub.** The codebase now lives at https://github.com/dangelojohn/alfacore (private, `dangelojohn` org). The Forgejo-shaped release pipeline (`.forgejo/workflows/`) was retired in favor of GitHub Actions (`.github/workflows/`). All 7 references to `forgejo.realpartners.tld` were replaced.
- **All 14 AlfaCore Odoo modules are installed on a live QNAP Odoo 19 instance** at `192.168.68.108` (Container Station, Caddy-fronted on `:9443`). Multiple Odoo-16-to-19 compatibility fixes were required to get there.
- **A new opt-in sub-module `alfa_core_loaner_sign`** was created to isolate the Enterprise `sign` dependency. Base `alfa_core_loaner` now installs on Community Edition.
- **Every module now has the Alfa Romeo crest as its Odoo Apps icon** (`static/description/icon.png`, 512×512 PNG).
- **GitHub Actions CI is wired up**: `lint`, `validate`, `test` (Odoo 19 matrix), `build` (GHCR addon-loader image), `sign` (Cosign + GitHub Releases). Five workflows total.
- **An end-to-end mock harness** for the release-upload curl flow was built and then retired with the Forgejo→GitHub migration.

---

## 1. Live deployment — QNAP `192.168.68.108`

Owner: `admin@192.168.68.108` (SSH, key auth from `naadmin`'s `~/.ssh/id_ed25519`). The QNAP hostname is `SoundCloud`. **Note:** older docs referenced `192.168.0.30` — that address is stale. The current host is `192.168.68.108` on the `192.168.68.0/24` LAN.

### 1.1. Containers (Container Station, system-docker socket)

| Container | Image | Purpose |
|---|---|---|
| `alfacore-postgres` | `postgres:16` | DB; data at `/share/CACHEDEV3_DATA/Container/odoo/postgres-data` |
| `alfacore-odoo` | `odoo:19` (CE, `19.0-20260504`) | App server; addons mount at `/share/CACHEDEV3_DATA/Container/odoo/addons:/mnt/extra-addons` |
| `alfacore-caddy` | `caddy:2` | Reverse proxy + TLS termination; container `:80`/`:443` mapped to host `:9080`/`:9443` (because QTS owns 80/443) |
| `alfacore-forgejo` | `codeberg.org/forgejo/forgejo:11` | Up but **never went through first-time setup** — the deploy/ ConfigMaps that used to point here have been migrated to GitHub |

All four have `restart: unless-stopped`. Compose at `/share/CACHEDEV3_DATA/Container/odoo/docker-compose.yml`.

### 1.2. URLs (external)

| What | URL | Notes |
|---|---|---|
| Odoo web | `https://192.168.68.108:9443/web/login` | Self-signed cert (first visit needs acceptance) |
| Odoo HTTP | `http://192.168.68.108:9080/web/login` | Plain HTTP fallback |
| AlfaCore PWA REST | `https://192.168.68.108:9443/api/v1/*` | Endpoints: `/auth` POST, `/scans` POST, `/diagnoses/{id}`, `/vehicles/{vin}/preferences`, `/vehicles/{vin}/recalls` |
| Module icons | `https://192.168.68.108:9443/<module>/static/description/icon.png` | 200 OK confirmed for sampled modules |
| Forgejo (unconfigured) | `https://192.168.68.108:9443/git/` | First-run install page |
| QTS admin | `http://192.168.68.108:8080` or `https://192.168.68.108` (port 443 is QTS, NOT Caddy) | Don't confuse with Odoo |

### 1.3. Secrets present on the QNAP (cleartext in compose / odoo.conf)

- Postgres user `odoo` password: `UTToMhuxTgoZ3GEcr3ZymI5Me3T5vUwb`
- Odoo `admin_passwd` (DB manager): `exCbgKsx18EHtBopkZueswdrdvvcnPsn`
- Both are LAN-only and should be rotated before any external exposure.

### 1.4. Module install state — 14 of 14 AlfaCore modules INSTALLED

| Module | Status | Notes |
|---|---|---|
| `alfa_core` | installed | Application anchor |
| `alfa_fleet` | installed | Customer vehicles |
| `alfa_parts` | installed | Parts catalog |
| `alfa_service` | installed | Service orders, bays, quality |
| `alfa_core_scanner` | installed | OBD ingestion |
| `alfa_core_diagnosis` | installed | DTC corpus + triage engine |
| `alfa_core_configurator` | installed | Eligibility-rule orchestrator |
| `alfa_core_inspection` | installed | Digital inspection |
| `alfa_core_loaner` | installed | **Sign-free** in this CE deploy |
| `alfa_core_portal` | installed | Customer portal |
| `alfa_core_app_api` | installed | PWA REST API |
| `alfa_core_campaign` | installed | NHTSA recall pull |
| `alfa_tsb` | installed | TSB corpus (requires `qdrant_client` in container) |
| `alfa_core_multi_loc` | installed | P3 stub |
| **`alfa_core_loaner_sign`** | **not installable on CE** | New sub-module for the Sign integration; depends on Enterprise `sign` |

Verified by `SELECT name, state FROM ir_module_module WHERE name LIKE 'alfa_%'` against the live DB.

### 1.5. Python runtime additions inside `alfacore-odoo`

The base `odoo:19` image is missing several Python deps. These were installed via `pip install --break-system-packages` against the live container:

- `pyjwt` (for `alfa_core_app_api`)
- `numpy` (transitive for qdrant-client)
- `typing_extensions` (force-upgraded with `--ignore-installed` to bypass the Debian-managed RECORD lock)
- `qdrant-client` (for `alfa_tsb`)

**These do not persist across container recreate.** If the container is wiped and rebuilt from the base image, these need to be reinstalled. **The proper fix is a custom Dockerfile** that does `FROM odoo:19` + `RUN pip install --break-system-packages typing_extensions pyjwt qdrant-client numpy`. That hasn't been authored yet; it's a known outstanding item.

---

## 2. Source of truth — GitHub `dangelojohn/alfacore`

**Branch:** `main`. **HEAD:** `73a48d0`. **Visibility:** Private. **Owner:** `dangelojohn`.

Three preservation branches mirror older project states (never merged, kept as history snapshots):
- `claude-code-impl` — original sprints 1–13 baseline
- `claude-code-impl-pre-v2.4` — pre-v2.4 deploy + CI work
- `claude-code-impl-pre-v2.6` — pre-v2.6 cascade audit

### 2.1. Commits authored by Claude Code this session (in chronological order)

```
73a48d0  feat: split loaner Sign integration + add Alfa Romeo logo to all modules
a7cd2f2  fix: 2 follow-ups from QNAP install on Odoo 19.0-20260504
6728d75  fix: move scanner→diagnosis Many2one to diagnosis side (no circular dep)
9072fd2  fix(alfa_fleet): port search view to Odoo 19 group-by syntax
f9e5900  fix(alfa_core): port security groups to Odoo 19 privilege model
9bdb7e9  fix(alfa_core): drop sale_subscription dep (Enterprise-only, unused)
15ddd60  docs: add RELEASE-CHECKLIST.md (now partly stale due to Forgejo→GitHub migration)
158a52c  fix(corpus): revert 4 architectural-intent dep additions from 28cdd03
28cdd03  fix(corpus): align manifests + configurator naming (D10, D11)
bd36677  fix(ci): resolve CI workflow gaps (D5, D6, D7) — Forgejo era
2d086c1  fix(deploy): resolve prod overlay deploy-blockers (D1, D3, D4, D8)
e5a00be  build: enable release tarball build at v0.1.0-dev
80a8ac5  docs(findings): prod k8s overlay had 4 deploy/operational issues (now resolved)
a920ab7  fix(ci): two CI workflow bugs (Forgejo era; later migrated)
7541da0  fix(Makefile): three install/release-path bugs
1441079  docs(findings): CI workflow gaps (Forgejo era; later resolved)
c378da3  fix(deploy+ci): resolve D9 image path; verify D5 release upload
8fa2ccc  style+fix: ruff clean (lint config + auto-format + 4 real fixes)
```

Plus the Forgejo→GitHub migration commit and a few smaller follow-ups around it.

### 2.2. Migration to GitHub Actions

The original codebase shipped with `.forgejo/workflows/` targeting a `forgejo.realpartners.tld` host that doesn't exist in DNS. Migrated to `.github/workflows/`:

| Workflow | Trigger | Purpose |
|---|---|---|
| `lint.yml` | push to main, PR | ruff check + format + pylint-odoo |
| `validate.yml` | push to main, PR | Python compile, XML parse, manifest validity, XML ref cross-resolve, ACL CSV format |
| `test.yml` | push, PR | Odoo 19 test matrix (5 groups: foundation / agentic_core / service_ops / integrations / smoke_all) with Postgres service container |
| `build.yml` | tag `v*` push | Builds + pushes `ghcr.io/dangelojohn/alfacore-addon-loader:{tag,latest}` to GHCR using auto-provided GITHUB_TOKEN |
| `sign.yml` | tag `v*` push | Cosign-signs the module tarballs and uses `gh release create` to publish them as GitHub Release assets |

CI signal from the latest run on `8fa2ccc` (before the loaner split): validate ✅, lint ✅, test (foundation, agentic_core, service_ops, integrations) all ✅. `smoke_all` was still in progress when monitoring stopped.

Two GitHub repo secrets required for release pipeline (P2 in RELEASE-CHECKLIST):
- `ALFACORE_COSIGN_KEY` — private key body
- `ALFACORE_COSIGN_PASSWORD` — its password

`GITHUB_TOKEN` is auto-provided by Actions; no PAT needed for release create / asset upload.

---

## 3. Odoo 19 portability fixes (by category)

The codebase was originally drafted against Odoo 16/17 patterns. The QNAP runs Odoo 19.0-20260504 (CE Docker image). Five distinct API breakages were fixed in code; one was bypassed at deploy time.

### 3.1. `sale_subscription` dep dropped (commit `9bdb7e9`)

`alfa_core` declared `sale_subscription` (Odoo Enterprise) but never referenced it in code — AlfaCore has its own `alfa_core.subscription` model. Manifest entry was scaffolding from an earlier design. Removed cleanly.

### 3.2. `res.groups.category_id` → `res.groups.privilege.privilege_id` (commit `f9e5900`)

Odoo 19 dropped `category_id` from `res.groups` and introduced a `res.groups.privilege` intermediary record that carries the `ir.module.category` reference. The 4 AlfaCore security groups (`User`, `Service Advisor`, `Service Manager`, `PIPEDA Privacy Officer`) were ported by:
1. Adding one `res.groups.privilege` record named `alfa_core_privilege` with the category
2. Each group now uses `privilege_id` instead of `category_id`

UI behavior preserved: all 4 groups still appear under "AlfaCore" in Settings → Users & Companies → Permissions.

### 3.3. Search view `<group expand="0">` → `<separator/>` + top-level filters (commit `9072fd2`)

Odoo 19's RelaxNG validator rejects the `expand` attribute on `<group>` and requires Group-By filters to live at the search-view top level, not wrapped in a `<group>`. Only `alfa_fleet/views/vehicle_views.xml` had this pattern.

### 3.4. Cross-module Many2one circular dep (commit `6728d75`)

`alfa_core_scanner.scan_session` declared `diagnosis_report_id` → `alfa_core_diagnosis.report`. This is a circular dep because `alfa_core_diagnosis` depends on `alfa_core_scanner`. Fix: moved the field into `alfa_core_diagnosis/models/scan_session.py` via `_inherit`. The view fragment was likewise moved to `alfa_core_diagnosis/views/scan_session_views.xml` with xpath-inherit.

### 3.5. `hr.employee` references (commit `a7cd2f2`)

`alfa_core_diagnosis.report.reviewed_by_id` was a Many2one to `hr.employee` but the manifest didn't declare `hr`. Changed to `res.users` (semantically more correct — "Pro Reviewer" is a user-role concept). Other modules that legitimately use `hr.employee` (inspection, loaner, service) already had `hr` in their manifests.

### 3.6. `view_session_form` ID mismatch (commit `a7cd2f2`)

The new scan_session view inheritance referenced `alfa_core_scanner.view_scan_session_form` but the actual ID is `alfa_core_scanner.view_session_form`. Local CI (`tools/ci/check_xml_refs.py`) caught it on the next `make tarball`.

### 3.7. Enterprise `sign` dependency split out (commit `73a48d0`)

This was the biggest change. `alfa_core_loaner` declared `sign` in its dependencies — but `sign` is Odoo Enterprise, not in CE. Split into:

**`alfa_core_loaner` (base, CE-installable):**
- Core allocation logic, state machine (draft → scheduled → active → returned → completed)
- Vehicle assignment, pickup/return condition reports, mileage tracking
- No e-signature flow

**`alfa_core_loaner_sign` (new EE-only sub-module):**
- `_inherit alfa_core_loaner.allocation` and adds:
  - `sign_request_id` Many2one → `sign.request`
  - `sign_status` Selection (not_sent / sent / signed / expired)
  - `action_send_for_signature` method (generates `sign.request` from template)
  - `_sync_sign_status` + `cron_sync_pending_signatures` (5-min poll)
  - Overrides `action_activate` to require `sign_status == "signed"` before pickup
  - Overrides `action_cancel` to also cancel pending `sign.request`
- `data/sign_config.xml` (ir.config_parameter placeholders for template_id + signer role)
- `data/cron.xml` (the sync cron)
- `views/loaner_allocation_views.xml` (xpath-inherit re-injects the Sign UI)
- `tests/test_sign_integration.py` (moved from base)

Effect: CE deploys get full loaner workflow minus e-signatures. EE deploys install the overlay for the complete v2.9 functionality.

### 3.8. Known but unfixed: `_sql_constraints` deprecation

Odoo 19 warns: `Model attribute '_sql_constraints' is no longer supported, please define models.Constraint on the model.` Currently a WARNING in the log, not an error — 21 occurrences across the codebase. Not blocking install. Future-proofing requires migration to `models.Constraint`.

### 3.9. Known but unfixed: `tracking=True` on `alfa_core_diagnosis.dtc.severity`

Odoo 19 warns: `unknown parameter 'tracking'`. Single field; doesn't block install but should be removed or replaced with proper auditlog wiring.

### 3.10. Known but unfixed: `@route(type='json')` deprecation

`alfa_core_app_api/controllers/api_v1.py` uses `type='json'` (two occurrences). Odoo 19 deprecated this in favor of `type='jsonrpc'`. Still functional; should be migrated.

---

## 4. Visual / branding work

### 4.1. Alfa Romeo logo as Odoo Apps icon

A 512×512 Alfa Romeo crest PNG (46,767 bytes) was placed at `static/description/icon.png` in all 15 modules (14 AlfaCore + the new `alfa_core_loaner_sign` overlay). HTTP probes confirm icons serve 200 from Caddy on the QNAP. The Odoo Apps screen at `https://192.168.68.108:9443/odoo/apps` shows the crest on every AlfaCore module.

Source file lives at `static/description/icon.png` in each module. The user's source was `/Users/naadmin/Downloads/Alfa-Romeo-Logo.png`.

---

## 5. Configuration / decisions made by Claude Code

These are durable judgments encoded in the codebase. Claude.ai should treat them as binding unless the architecture corpus updates.

### 5.1. Prod overlay decoupled from multi-replica HA (commit `2d086c1`)

The prod K8s overlay originally promised `replicas: 2` + RollingUpdate, but the base `odoo-filestore` PVC is RWO and there's no session affinity. Decision (Pattern 10 — honest boundaries): drop to `replicas: 1` with Recreate strategy. Multi-replica HA is deferred until either an RWX storage class, S3-backed `ir_attachment.location`, or Redis `session_store` is in play.

### 5.2. Workers reduced 4 → 3 in prod overlay (commit `2d086c1`)

`workers = 4` × per-worker hard limit 2.5 GiB summed to 10 GiB against an 8 GiB pod limit. K8s would OOM-kill before Odoo's recycle. Lowered to 3.

### 5.3. Manifests track what code uses, not what corpus describes (commit `158a52c`)

The Application-Architecture-Blueprint dep graph anticipates several dependencies that aren't yet exercised by code (e.g., `alfa_core_diagnosis` "should" depend on `alfa_tsb` per corpus, but no code in diagnosis touches tsb models). Decision: manifests declare what's wired today; corpus describes intended end state. When downstream features actually land, the dep gets added then.

The one exception is `alfa_core_configurator` which DID have a real declared-vs-used mismatch (`alfa_service` declared but `alfa_fleet.vehicle` used) — that was fixed in commit `28cdd03`.

### 5.4. CI smoke matrix as a 5th matrix group (commit `bd36677`)

`test.yml` now has a `smoke_all` matrix entry that runs `alfacore_smoke`-tagged tests across all 14 modules in one job — independent of the sprint-tagged per-group runs. This was originally CI gap D6.

### 5.5. `alfa_core_diagnosis.report.reviewed_by_id` is a `res.users`, not `hr.employee`

See 3.5 above. A "Pro reviewer" is conceptually a user role; tying it to an employee record would require pulling in the `hr` module unnecessarily. If/when AlfaCore wants employee-level metadata on reviewers, add a computed `reviewer_employee_id` via `user_id.employee_id`.

### 5.6. RELEASE-CHECKLIST.md describes the path but is partly stale

`docs/RELEASE-CHECKLIST.md` was written when the release pipeline targeted Forgejo. The Forgejo→GitHub migration in `73a48d0` makes some sections wrong (GitHub doesn't need `FORGEJO_TOKEN`; the addon-loader is on GHCR; release assets are GitHub Releases not Forgejo Releases). Sections P1 (image path) and the 7-step procedure are correct in spirit but need URL/host updates.

---

## 6. Verification status — what's actually been tested

| Verification | Result | Method |
|---|---|---|
| Static stack | ✅ green | `make tarball` → 14 manifests valid, 298 XML IDs cross-resolve |
| Ruff lint | ✅ green | `ruff check .` → All checks passed (after the lint cleanup in `8fa2ccc`) |
| YAML parse, workflow files | ✅ green | All 5 `.github/workflows/*.yml` parse via `yaml.safe_load` |
| Bash syntax, workflow run blocks | ✅ green | All 19 embedded bash blocks pass `bash -n` |
| GitHub Actions — validate / lint | ✅ green | Real runs on `8fa2ccc` |
| GitHub Actions — test (4 of 5 matrix legs) | ✅ green | foundation / agentic_core / service_ops / integrations all passed on `7dea424` |
| GitHub Actions — test (smoke_all leg) | ⏳ in progress when monitoring stopped | Was ~24min in; sibling legs took 3-5min each so this leg is genuinely slower (14 modules vs 3-4) |
| QNAP runtime install (all 14 alfa_* modules) | ✅ green | `SELECT state FROM ir_module_module` shows all installed |
| QNAP web endpoints | ✅ green | `/web/login`, `/web/health`, `/web/database/manager` all HTTP 200 |
| QNAP icon serving | ✅ green | 4-of-15 sampled icons served HTTP 200 |
| QNAP `-u` upgrade of all modules | ✅ EXIT=0 | `odoo -d alfacore -u <all 14>` completed clean |
| `alfacore_smoke` test suite against live QNAP | ⚠ partial | Smoke run started; loaded all 14 modules cleanly; one Traceback at line 182 of `/tmp/smoke.out` not yet root-caused (exit 255 reported but logs show "Modules loaded" + "Registry loaded in 30.596s") |

The one outstanding item is the smoke-suite exit-code 255 with a Traceback. Worth investigating in the next session, but the modules themselves are confirmed installable and the runtime is operational.

---

## 7. Outstanding items — what hasn't been done

### 7.1. Custom `odoo:19` Docker image with deps baked in

The Python deps (`pyjwt`, `numpy`, `typing_extensions`, `qdrant-client`) were installed via `pip install` against the running container. They survive `docker restart` but NOT `docker compose down && docker compose up` or any image rebuild. The proper fix:

```dockerfile
FROM odoo:19
USER root
RUN pip install --break-system-packages --ignore-installed typing_extensions && \
    pip install --break-system-packages pyjwt qdrant-client numpy
USER odoo
```

Build, push to GHCR (or local registry), update `docker-compose.yml` on the QNAP. Until then, document the manual `docker exec ... pip install ...` step in a runbook.

### 7.2. Real first release cut

No `v*` tag has been pushed. The GitHub Actions `build.yml` + `sign.yml` workflows have never run end-to-end. The mock harness (`tools/dev/release-pipeline-mock/`) was retired in the Forgejo→GitHub migration; the new flow uses `gh release create` which is too well-tested upstream to need a mock.

### 7.3. `_sql_constraints` modernization

21 occurrences. Currently warnings only. Should be migrated to `models.Constraint` for Odoo 19+ compatibility.

### 7.4. `@route(type='json')` → `type='jsonrpc'`

Two occurrences in `alfa_core_app_api/controllers/api_v1.py`. Currently DeprecationWarning.

### 7.5. `alfa_core_diagnosis.dtc.severity` — drop `tracking=True`

Single field, Selection-typed. Odoo 19 doesn't accept tracking on this field shape.

### 7.6. Forgejo on QNAP — never configured

The `alfacore-forgejo` container is Up but the install wizard was never completed. Since the codebase is now on GitHub, this is no longer a release-path blocker. If/when the team wants a self-hosted git mirror, hit `https://192.168.68.108:9443/git/` and walk through the setup.

### 7.7. RELEASE-CHECKLIST.md update

Sections referring to Forgejo (P2 secrets, step 5 asset URLs) need rewriting against the GitHub Actions + Releases flow.

### 7.8. `addon-loader` GitHub Release auth on private repo

The `addon-loader/entrypoint.sh` now requires a `GITHUB_TOKEN` env var because GitHub Releases on private repos are auth-gated. The k8s Secret `alfacore-github-token` is referenced in `deploy/k8s/base/odoo-deployment.yaml` and the dev/prod overlays. Operator action: generate a fine-grained PAT scoped to `dangelojohn/alfacore` Contents:Read, load as a k8s Secret. Not relevant to the QNAP docker-compose deploy.

---

## 8. Recommendations to Claude.ai

### 8.1. Treat the GitHub repo as the canonical source

GitHub `dangelojohn/alfacore` is now the source of truth. Forgejo-shaped artifacts in old chats are stale.

### 8.2. The QNAP IP changed; ignore `192.168.0.30`

Older REALPublish documentation references `192.168.0.30` for the QNAP. That's stale. Current: `192.168.68.108`. Saved to Claude Code's auto-memory at `qnap_alfacore_stack.md`.

### 8.3. The Sign integration is now optional

When future work touches loaner allocation, remember the split: any new field that uses `sign.*` models belongs in `alfa_core_loaner_sign`, NOT base `alfa_core_loaner`. Base must remain CE-installable. The xpath-inherit pattern in `alfa_core_loaner_sign/views/loaner_allocation_views.xml` shows how to inject UI from the overlay.

### 8.4. Odoo 19 is stricter than 16/17 — preflight new XML views

Three Odoo 19 view/security/data XML changes have been encountered so far:
- `res.groups`: no `category_id`; use `res.groups.privilege` intermediary
- Search views: no `<group expand=>`; Group-By filters at top level after `<separator/>`
- `_sql_constraints` deprecated → `models.Constraint`

When authoring new modules, check that views/security follow Odoo 19 patterns from the start.

### 8.5. The QNAP deploy doesn't use the k8s manifests

`deploy/k8s/` is set up for a real Kubernetes deploy. The QNAP runs `docker-compose.yml` at `/share/CACHEDEV3_DATA/Container/odoo/docker-compose.yml`. They share the addon-loader / Caddy pattern conceptually but the QNAP version is a different, hand-edited compose file (not generated from k8s). Changes to deploy manifests in the repo don't automatically reflect on the QNAP — the QNAP is rsync'd by hand from this Mac's working tree.

### 8.6. The architecture corpus is binding but not always reflected in code yet

CLAUDE.md says the six docs in `docs/architecture/` are authoritative. Several gaps exist between what they describe and what the manifests currently declare — see decision 5.3. Don't auto-add manifest deps to "match corpus"; verify each is exercised by real code first.

### 8.7. Test on real Odoo 19, not just static checks

The GitHub Actions test matrix uses `odoo/odoo@19.0` branch from source, which has cumulative changes the `19.0-20260504` Docker image doesn't. Multiple bugs were missed by static checks but caught by the QNAP install attempts (`category_id`, `expand`, circular Many2one). When authoring fixes, ideally validate against both:
- Static: `make tarball` (manifests + XML refs + py_compile)
- Dynamic-CI: GitHub Actions on a push (Odoo 19 dev branch)
- Dynamic-prod: the QNAP install (`odoo:19` release tag)

---

## 9. File / path reference

| What | Where |
|---|---|
| Repo on this Mac | `/Users/naadmin/work/alfacore` |
| Repo on GitHub | https://github.com/dangelojohn/alfacore (private) |
| Modules on QNAP | `admin@192.168.68.108:/share/CACHEDEV3_DATA/Container/odoo/addons/` |
| Compose on QNAP | `admin@192.168.68.108:/share/CACHEDEV3_DATA/Container/odoo/docker-compose.yml` |
| Odoo.conf on QNAP | `admin@192.168.68.108:/share/CACHEDEV3_DATA/Container/odoo/config/odoo.conf` |
| Filestore on QNAP | `admin@192.168.68.108:/share/CACHEDEV3_DATA/Container/odoo/odoo-data/` |
| Logs on QNAP | `admin@192.168.68.108:/share/CACHEDEV3_DATA/Container/odoo/logs/odoo.log` |
| Claude Code's auto-memory | `/Users/naadmin/.claude/projects/-Users-naadmin/memory/` |
| This document | `docs/CLAUDE-CODE-HANDOFF-2026-05-12.md` (i.e. `/Users/naadmin/work/alfacore/docs/CLAUDE-CODE-HANDOFF-2026-05-12.md`) |

---

## 10. How to keep both Claude.ai and Claude Code in sync going forward

- **Anything Claude.ai authors as a tarball drop:** continue the v2.x → v2.y pattern. Claude Code will apply each drop using the established branch+replace workflow (preserving prior work on a date-stamped branch).
- **Anything Claude Code changes locally:** committed + pushed to GitHub `main`. Look at `git log` since this snapshot's `73a48d0` for the latest.
- **The QNAP runtime:** the rsync from this Mac is the deploy mechanism. Re-running `rsync -a --no-perms ... /Users/naadmin/work/alfacore/ admin@192.168.68.108:/share/CACHEDEV3_DATA/Container/odoo/addons/` + `chown -R 100:101 ... + docker restart alfacore-odoo` picks up any code change. Module-level `-u` is needed for view/data changes.

---

*End of handoff.*
