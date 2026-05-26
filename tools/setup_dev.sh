#!/usr/bin/env bash
# AlfaCore developer onboarding — one-shot.
#
# Idempotent: safe to re-run. Each step checks whether it's already done
# and skips quietly.
#
# What it does:
#   1. Verifies Python 3.11+ is available
#   2. Installs pre-commit if missing
#   3. Installs pre-commit hooks into .git/hooks
#   4. Ensures alfacore.cosign.pub is real (not the placeholder)
#   5. Runs the validator scripts to confirm the repo is clean
#
# What it does NOT do:
#   - Start the dev stack (use `make dev-up` for that)
#   - Install Docker (assumed present)
#   - Configure your editor

set -euo pipefail

# Colors (skip if not a TTY)
if [ -t 1 ]; then
    RED=$(tput setaf 1); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4); RESET=$(tput sgr0)
else
    RED=""; GREEN=""; YELLOW=""; BLUE=""; RESET=""
fi

ok()    { echo "${GREEN}✓${RESET} $1"; }
info()  { echo "${BLUE}•${RESET} $1"; }
warn()  { echo "${YELLOW}!${RESET} $1"; }
fail()  { echo "${RED}✗${RESET} $1" >&2; exit 1; }

# Must be in the repo root
[ -f "pyproject.toml" ] || fail "Run this from the AlfaCore repo root."

# -----------------------------------------------------------------------------
echo "${BLUE}== AlfaCore dev setup ==${RESET}"

# 1. Python version
info "Checking Python..."
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
    fail "Python 3.11+ required, found $PY_VERSION"
fi
ok "Python $PY_VERSION"

# 2. pre-commit
info "Checking pre-commit..."
if ! command -v pre-commit >/dev/null 2>&1; then
    info "pre-commit not found, installing..."
    if command -v pipx >/dev/null 2>&1; then
        pipx install pre-commit
    else
        python3 -m pip install --user pre-commit
    fi
fi
ok "pre-commit installed: $(pre-commit --version)"

# 3. Install hooks
info "Installing pre-commit hooks..."
if [ ! -d .git ]; then
    warn "Not a git repo yet — skipping hook installation."
    warn "After `git init`, run `pre-commit install` manually."
else
    pre-commit install >/dev/null
    ok "Hooks installed into .git/hooks/"
fi

# 4. Cosign pubkey check
info "Checking Cosign keypair..."
if [ ! -f alfacore.cosign.pub ]; then
    warn "alfacore.cosign.pub not found."
    info "Generate the keypair with: make cosign-gen"
elif grep -q "PLACEHOLDER" alfacore.cosign.pub; then
    warn "alfacore.cosign.pub is the placeholder."
    info "Replace with a real keypair before any release tag:"
    info "  make cosign-gen"
else
    ok "Real Cosign public key committed."
fi

# 5. Validator dry-run
info "Running validators against current repo state..."
python3 tools/ci/check_manifests.py >/dev/null && ok "manifests valid"
python3 tools/ci/check_manifest_files.py >/dev/null && ok "manifest-referenced files exist"
python3 tools/ci/check_xml_refs.py >/dev/null && ok "XML IDs cross-resolve"

echo ""
echo "${GREEN}Setup complete.${RESET} Useful next commands:"
echo "  ${BLUE}make help${RESET}        list every available target"
echo "  ${BLUE}make dev-up${RESET}      start Odoo + Postgres + Qdrant + Ollama locally"
echo "  ${BLUE}make validate${RESET}    re-run validators anytime"
echo "  ${BLUE}make test-local${RESET}  run Odoo tests against the running stack"
