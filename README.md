# AlfaCore

Luxury automotive service platform for Italian-platform vehicles (Alfa Romeo
in v1; Fiat / Maserati in v1.1+). Paired OBD-II BLE scanner + companion PWA +
AI diagnosis backed by Odoo 19 CE. Built on the Twelve Patterns engineering
doctrine from ANDREW v2 Part X.

**13 Odoo modules · ZDE-first · LGPL-3 · audit-ready by construction · GitOps-deployed**

## Quick start

```bash
# One-time setup
bash tools/setup_dev.sh
make cosign-gen           # generate the signing keypair (one-time)

# Daily loop
make dev-up               # start Odoo + Postgres + Qdrant + Ollama locally
make validate             # run all repo validators
make test-local MODULE=alfa_core    # run a single module's tests
make dev-down             # stop the local stack
```

Run `make help` for the full command surface.

## What's inside

| Layer | Where | Purpose |
|---|---|---|
| **Modules** | `alfa_*/` | The 13 Odoo modules — see `docs/SPRINT-IMPLEMENTATION-STATUS.md` |
| **Architecture** | `docs/` | Service Plan, JTBD Gap Analyses, Application Architecture Blueprint, Decision Log |
| **CI/CD** | `.github/workflows/` | validate / lint / test / build / sign workflows |
| **Pre-commit** | `.pre-commit-config.yaml` | same validators run locally on every git commit |
| **Validators** | `tools/ci/check_*.py` | manifest sanity, XML-ID cross-reference, file-existence |
| **Deployment** | `deploy/` | Kustomize base + dev/prod overlays + Argo CD Applications |
| **Init-container** | `addon-loader/` | Cosign-verifying init-container source |
| **Dev stack** | `docker-compose.dev.yml` | local Odoo + Postgres + Qdrant + Ollama |

## The patterns

This codebase encodes the Twelve Patterns from ANDREW v2 Part X:

1. **Finite pipeline stages with observability** — Sprint 4 `sale_order` 15-state machine
2. **Auto-detect over config, fail loud** — Sprint 2 VIN regex validation
3. **Anchor-text extraction (labels=API)** — Sprint 1 plan `code` field is the API key
4. **Per-record isolation** — Sprint 2 `alfa_fleet.vehicle` VIN unique
5. **Idempotent timestamped intermediates** — Sprint 5 `scan_session` immutable once committed
6. **Configuration-as-data** — Sprint 7 `eligibility_rule` domain expressions
7. **`canon_label` 7-pass canonicalization** — Sprint 3 `canonicalize_part_number()`
8. **Information budgets per stage** — Sprint 6 `confidence` field
9. **Logging as UI** — Sprint 1 chatter; Sprint 7 `benefit_ledger`; Sprint 12 notification trail
10. **Honest boundaries** — Sprint 3 alternative `grade` enum (`not_recommended` is a real option); Sprints 11/12/13 stub methods document hand-off boundaries explicitly
11. **Per-record privacy disposition** — `inference_zde` inherited across subscription → scan → diagnosis → inspection
12. **Versioned content** — Sprint 1 `pipeda_consent_version`; Sprint 8 inspection `template_version` snapshot

See `docs/SPRINT-IMPLEMENTATION-STATUS.md` for the full sprint × pattern map.

## License

LGPL-3.0-only. © REAL Partners Ltd. / OdooIQ.
