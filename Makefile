# AlfaCore Makefile — common dev commands.
#
# Run `make` or `make help` to see what's available.

.DEFAULT_GOAL := help
.PHONY: help validate test-syntax test-local tarball clean
.PHONY: dev-up dev-down dev-shell dev-logs dev-restart dev-reset
.PHONY: pre-commit-install pre-commit-run setup
.PHONY: cosign-gen cosign-show

# Tunable: which module to operate on for module-scoped targets
MODULE ?= alfa_core
# Tunable: which Odoo DB to use locally
DEV_DB ?= alfacore_dev


help:  ## Show this help
	@echo "AlfaCore — dev command surface"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Variables:"
	@echo "  MODULE=<name>    target a specific module (default: alfa_core)"
	@echo "  DEV_DB=<dbname>  Odoo database name to use locally (default: alfacore_dev)"

# -----------------------------------------------------------------------------
# Validation — local, fast, the same checks CI runs
# -----------------------------------------------------------------------------

validate: test-syntax  ## Run every validator: syntax + manifests + XML refs
	@python3 tools/ci/check_manifests.py
	@python3 tools/ci/check_manifest_files.py
	@python3 tools/ci/check_xml_refs.py

test-syntax:  ## Python compile + XML parse + CSV header check
	@echo "[1/3] Python compile..."
	@find alfa_* -name "*.py" -print0 | xargs -0 python3 -m py_compile && echo "      OK"
	@echo "[2/3] XML parse..."
	@find alfa_* -name "*.xml" | while read f; do \
		python3 -c "import xml.etree.ElementTree as ET; ET.parse('$$f')" || exit 1; \
	done && echo "      OK"
	@echo "[3/3] CSV header check..."
	@for csv in $$(find alfa_* -name "ir.model.access.csv"); do \
		head -1 "$$csv" | tr -d '"' | grep -q "perm_read,perm_write,perm_create,perm_unlink" || { echo "FAIL: $$csv"; exit 1; }; \
	done && echo "      OK"

# -----------------------------------------------------------------------------
# Local Odoo testing (requires the docker-compose stack to be running)
# -----------------------------------------------------------------------------

test-local: dev-up-quiet  ## Run Odoo tests for $(MODULE) against the local stack
	docker compose -f docker-compose.dev.yml exec -T odoo \
		odoo-bin -d $(DEV_DB)_$(MODULE) -i $(MODULE) \
			--test-enable --stop-after-init \
			--log-level=info

test-all-modules: dev-up-quiet  ## Run tests for every module in sequence
	@for mod in alfa_core alfa_fleet alfa_parts alfa_service \
	            alfa_core_scanner alfa_core_diagnosis alfa_core_configurator \
	            alfa_core_inspection alfa_core_loaner alfa_core_portal \
	            alfa_core_app_api alfa_core_campaign alfa_tsb; do \
		echo "=== Testing $$mod ==="; \
		MODULE=$$mod $(MAKE) test-local || exit 1; \
	done

# -----------------------------------------------------------------------------
# Release packaging
# -----------------------------------------------------------------------------

tarball: validate  ## Build a release tarball (validates first)
	@mkdir -p dist
	@VERSION=$$(grep -E '^version' pyproject.toml | head -1 | sed 's/.*= "\(.*\)"/\1/'); \
	VERSION=$${VERSION:-dev}; \
	tar --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' \
		--exclude='dist' --exclude='*.tar.gz' \
		-czf "dist/alfacore-modules-$$VERSION.tar.gz" alfa_*; \
	echo "Built dist/alfacore-modules-$$VERSION.tar.gz"; \
	cd dist && { sha256sum "alfacore-modules-$$VERSION.tar.gz" 2>/dev/null \
		|| shasum -a 256 "alfacore-modules-$$VERSION.tar.gz"; }

clean:  ## Remove pycache, dist, build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf dist/ build/ *.egg-info/

# -----------------------------------------------------------------------------
# Local docker-compose dev stack
# -----------------------------------------------------------------------------

dev-up:  ## Start the local dev stack (Postgres + Odoo + Qdrant + Ollama)
	docker compose -f docker-compose.dev.yml up -d
	@echo ""
	@echo "AlfaCore dev stack is up:"
	@echo "  Odoo:    http://localhost:8069"
	@echo "  Qdrant:  http://localhost:6333/dashboard"
	@echo "  Ollama:  http://localhost:11434"
	@echo ""
	@echo "Database 'alfacore_dev' will be initialized on first browser hit."

dev-up-quiet:  # Internal: bring stack up without the banner
	@docker compose -f docker-compose.dev.yml up -d >/dev/null 2>&1

dev-down:  ## Stop the dev stack (keeps volumes)
	docker compose -f docker-compose.dev.yml down

dev-reset:  ## Tear down the dev stack AND wipe volumes (destructive)
	@read -p "This destroys the dev DB and filestore. Type 'yes' to confirm: " ans && [ "$$ans" = "yes" ]
	docker compose -f docker-compose.dev.yml down -v

dev-restart:  ## Restart just the Odoo container (after Python changes)
	docker compose -f docker-compose.dev.yml restart odoo

dev-shell:  ## Open a shell inside the running Odoo container
	docker compose -f docker-compose.dev.yml exec odoo bash

dev-logs:  ## Tail Odoo logs
	docker compose -f docker-compose.dev.yml logs -f odoo

# -----------------------------------------------------------------------------
# Pre-commit
# -----------------------------------------------------------------------------

pre-commit-install:  ## Install pre-commit hooks into .git/hooks/
	pre-commit install

pre-commit-run:  ## Run all pre-commit hooks against every file (not just diff)
	pre-commit run --all-files

# -----------------------------------------------------------------------------
# Cosign keypair management
# -----------------------------------------------------------------------------

cosign-gen:  ## Generate the Cosign keypair (one-time, replaces alfacore.cosign.{pub,key})
	bash tools/setup_cosign.sh

cosign-show:  ## Print the current public key
	@cat alfacore.cosign.pub

# -----------------------------------------------------------------------------
# One-shot developer onboarding
# -----------------------------------------------------------------------------

setup:  ## First-time setup for a new dev/machine (pre-commit + cosign + validate)
	bash tools/setup_dev.sh
