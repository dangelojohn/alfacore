# AlfaCore — Operational Pre-Flight Checklist

**Complete every item before the first tagged release.**

Items are grouped by phase. Each item is checked off by the person responsible; the date and operator initials should be recorded against each one in a real ops run.

---

## Phase A — Repository setup (day 1)

- [ ] **Architecture corpus complete in `docs/architecture/`**
    - All six markdown files present
    - `Alfa-Odoo-Server-Plan-v1.0.md` is NOT the placeholder version (check first H1)
    - Each file's metadata frontmatter matches the corpus version (`v1.0`)
- [ ] **`CLAUDE.md` committed at repo root** — durable Claude Code context
- [ ] **`README.md` reviewed** — accurate install path, correct Odoo version, correct module count (14)
- [ ] **Forgejo repository created** and pushed
- [ ] **Branch protection on `main`** — require PR review, require CI pass

## Phase B — CI/CD setup (day 1–2)

- [ ] **Forgejo Actions enabled** for the repo
- [ ] **Cosign keypair generated** via `bash tools/setup_cosign.sh`
- [ ] **`alfacore.cosign.pub` committed** to the repo
- [ ] **`alfacore.cosign.key` stored offline** (1Password, hardware vault) and working copy securely deleted
- [ ] **Forgejo repo secrets configured:**
    - `ALFACORE_COSIGN_KEY` — contents of the private key
    - `ALFACORE_COSIGN_PASSWORD` — the password set during generation
- [ ] **Lint workflow passes** on a test PR — `ruff` + `pylint-odoo`
- [ ] **Test workflow scaffolded** with Postgres service container; Odoo 19 Enterprise checkout path configured
- [ ] **Build workflow runs** on a test tag (e.g., `v0.0.1-test`) — produces module tarballs
- [ ] **Sign workflow runs** on the test tag — produces `.sig` artifacts; verify with public key

## Phase C — Knowledge workspace seeding (day 2–3)

- [ ] **Odoo 19 Enterprise installed** on dev substrate
- [ ] **`alfa_core` module installed** (`odoo-bin -i alfa_core`)
- [ ] **Knowledge module installed** (transitively pulled by `alfa_core`)
- [ ] **`tools/seed_knowledge.py` executed** against dev DB — workspace created, articles populated
- [ ] **Verify workspace visible** to operator personas; sensitive PII not exposed

## Phase D — Substrate readiness (day 3–5)

- [ ] **QNAP Docker stack running** per v1.0 Plan substrate spec
- [ ] **Traefik routing configured** for the AlfaCore subdomain
- [ ] **Coolify managing the lifecycle** of the AlfaCore container
- [ ] **PostgreSQL 15+ configured** with `dbfilter` and `list_db = False`
- [ ] **Backup cron scheduled** — at minimum daily DB dump, weekly full
- [ ] **TLS certificate provisioned** (Let's Encrypt via Traefik)
- [ ] **Tailscale Funnel** (or equivalent) configured if public exposure is needed before substrate promotion

## Phase E — Third-party integrations (parallel)

- [ ] **NHTSA vPIC API access verified** — public API, no key needed; test a known VIN
- [ ] **Twilio account provisioned** — Canadian-routed phone number, SMS sending enabled
- [ ] **Twilio credentials stored** as Odoo system parameters or Forgejo secrets
- [ ] **Stripe test mode account ready** (architecture is processor-agnostic; this is the default at pilot)
- [ ] **Webhook endpoints reachable** from public internet for Twilio status callbacks and Stripe events

## Phase F — Hardware (Vgate + OBDLink) procurement

- [ ] **Vgate iCar Pro BLE 4.0 batch ordered** (target: pilot cohort + 50% spare)
- [ ] **OBDLink MX+ batch ordered** (target: Pro-tier customers + spares)
- [ ] **Pairing token cards designed and printed** — one per device
- [ ] **Unboxing kit assembled** — device, pairing card, welcome insert, return-shipping label
- [ ] **Inventory tracked** in `alfa_core.scanner.device` once `alfa_core_scanner` is implemented

## Phase G — Pilot readiness gate

- [ ] **Sprint 1 through Sprint N complete** (per AlfaCore Application Architecture Blueprint §11 phased deployment)
- [ ] **Smoke test suite green** on `main` branch
- [ ] **Pilot recruitment scoped** — 5–10 customers per Decision Log
- [ ] **PIPEDA consent documents reviewed by counsel** (real legal review, not just product-team review)
- [ ] **Privacy policy live** at the AlfaCore public surface
- [ ] **Pilot customer agreements drafted** — clear scope, clear data handling, clear exit
- [ ] **Pilot launch date confirmed** with all stakeholders

---

## Decision Log compliance checks

Cross-reference every config setting against the Decision Log:

- [ ] Variant Creation Mode is **Dynamically** on every service-configurable product
- [ ] Subscription plans (Basic / Premium / Pro) are the only three at v1
- [ ] AlfaCore is **Alfa-only** scoped at v1 (Fiat / Maserati v1.1+)
- [ ] Inference disposition is **rule-based** in `alfa_core_diagnosis` at v1 (no LLM calls)
- [ ] WhatsApp is **disabled** at v1; SMS + email only
- [ ] Substrate is on **QNAP** at v1 (cloud promotion gated to 50 customers OR resource ceiling)
- [ ] Benefit ledger carryover is **one period maximum**
- [ ] Configurator save-state TTL is **30 days with auto-extension on activity**
- [ ] Telephony is **Twilio SMS only** at v1 (no voice integration)
- [ ] License declaration is **LGPL-3** on every module manifest
- [ ] Category is **`Services/AlfaCore`** on every module
- [ ] i18n directories include **EN, FR, IT** stubs

---

## Failure escalation

If any check above fails at the wrong phase, halt advancement and log the deviation. Surface to architecture review before resuming.

Examples of decisions that must NOT silently drift:
- "Variant Creation Mode = Instantly because Dynamically was producing slow performance" → architecture review required; resolve via indexing or rule simplification, not by reversing the decision
- "Switched to AGPL because of contributor concerns" → corpus revision required; touches Decision Log
- "Added native iOS app build" → out-of-scope per CLAUDE.md; surface as new workstream

The Decision Log is binding. Deviations require re-versioning the corpus.

---

*Pre-Flight Checklist v1.0 — closes the operational gaps from scaffold v1.0.*
