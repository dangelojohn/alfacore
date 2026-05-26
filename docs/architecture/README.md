# AlfaCore Architecture Corpus

**The six-document architectural authority for AlfaCore v1.0.**

These files are the *engineering canonical* — they live in version control because Claude Code, Aider, future AI coding agents, and human engineers need filesystem access to them.

The *operational canonical* is the **AlfaCore Knowledge workspace** in Odoo, populated from these files via `tools/seed_knowledge.py`. Advisors, technicians, and ownership read documentation in Knowledge; engineering reads it here.

## The corpus, in reading order

1. **`Alfa-Odoo-Server-Plan-v1.0.md`** — substrate, base modules, the Twelve Patterns from ANDREW v2 Part X
2. **`AlfaCore-Service-Plan-v1.0.md`** — customer-facing service model, scanner pipeline, diagnosis engine
3. **`AlfaCore-JTBD-Gap-Analysis-v1.0.md`** — full-lifecycle JTBD audit (luxury dealership benchmark)
4. **`AlfaCore-Configurator-JTBD-Gap-Analysis-v1.0.md`** — Product Configurator audit, eligibility/recommendation architecture
5. **`AlfaCore-Application-Architecture-Blueprint-v1.0.md`** — master architecture, module composition, cascade specification
6. **`AlfaCore-Decision-Log-v1.0.md`** — twenty-four locked decisions

## Authority hierarchy (precedence on conflict)

1. **Twelve Patterns** (ANDREW v2 Part X) — non-negotiable engineering doctrine
2. **Decision Log** — twenty-four locked decisions; non-negotiable for v1.0
3. **Application Architecture Blueprint** — synthesizes everything below into the master design
4. **Gap Analyses** — audit findings; informs Blueprint
5. **Service Plan** — customer-facing service model
6. **Substrate Plan** — foundational infrastructure

If a downstream document contradicts an upstream one, upstream wins. If you find a contradiction, surface it before resolving it in code.

## Sync to Knowledge

After modifications, push to Odoo Knowledge:

```bash
python tools/seed_knowledge.py \
    --odoo-url http://localhost:8069 \
    --db alfacore_prod \
    --user admin \
    --password '...' \
    --corpus-dir docs/architecture
```

The seeder is idempotent — re-running updates existing articles rather than duplicating them.

## Versioning

Architecture changes follow the corpus' own versioning. A v1.1 corpus update implies coordinated re-versioning across all affected documents and a CHANGELOG entry. Do not edit corpus files casually; doc changes ripple into Knowledge, into Claude Code sessions, and into engineering work.
