# AlfaCore Release Checklist

Tracks the steps between "static-clean code on `main`" and "tagged
release running in production." Authored 2026-05-12 against commit
`158a52c`; update on each release cut.

The work split:
- **Code work** (manifests, models, tests, CI, deploy manifests) — owned
  by Claude Code / human engineering. Verified static-clean.
- **Operational work** (secrets, registry, Cosign, deploy) — owned by
  the operator. Not yet executed for this codebase.

## Verified (green)

These don't need re-checking unless code changes:

- 14 module manifests are valid Python and load (`tools/ci/check_manifests.py`)
- Every manifest-referenced data/demo file exists on disk (`tools/ci/check_manifest_files.py`)
- 294 XML record IDs cross-resolve — no dangling `ref="…"` (`tools/ci/check_xml_refs.py`)
- Every `.py` file in `alfa_*/` compiles
- Every `.xml` file in `alfa_*/` parses
- All 13 module ACL CSVs have the canonical 8-column header
- `make tarball` produces a clean `dist/alfacore-modules-<version>.tar.gz`
- 31 test files exist across 14 modules; sprint tags 1–13 plus the
  universal `alfacore_smoke` install-test tag are all referenced by
  `.github/workflows/test.yml`

## Verified (green) — additional items

- **D9 (Odoo image path): resolved.** Direct registry HTTPS probe
  confirmed `ghcr.io/odoo/odoo:19.0` does not exist (token endpoint
  returns DENIED). `docker.io/odoo:19.0` returns a valid manifest.
  Both references in `docker-compose.dev.yml` and
  `deploy/k8s/base/odoo-deployment.yaml` now point at `docker.io/odoo:19.0`.
- **sign.yml release upload** now uses `gh release create` from GitHub
  Actions — `gh` is preinstalled on `ubuntu-latest` runners and uses
  the auto-provided `GITHUB_TOKEN`. The earlier Forgejo-specific mock
  harness was retired as part of the Path G migration; the canonical
  signal is the first real tag push.
- **All 5 GitHub workflow YAML files parse**; all 19 embedded bash
  `run:` blocks pass `bash -n` syntax check.

## Open prerequisites (red — blocking release)

### P2. GitHub repo secrets

Set on https://github.com/dangelojohn/alfacore (Settings → Secrets and
variables → Actions):

| Secret | Source | Used by |
|---|---|---|
| `ALFACORE_COSIGN_KEY` | Contents of offline `alfacore.cosign.key` (private key file) | `.github/workflows/sign.yml` |
| `ALFACORE_COSIGN_PASSWORD` | Password for the private key | `.github/workflows/sign.yml` |

`GITHUB_TOKEN` is provided automatically by Actions — no PAT needed for
release create / asset upload from within the workflow. `GHCR_TOKEN` is
also automatic; `docker/login-action` uses the built-in token for
`packages: write`.

`alfacore.cosign.pub` (public key) is already committed at repo root.
Cosign signature verification in the addon-loader init-container
checks against this committed pubkey.

A separate `alfacore-github-token` Kubernetes Secret is also required
at deploy time (lets the addon-loader pull from the private repo's
Release assets). Generate a fine-grained PAT at
https://github.com/settings/personal-access-tokens/new — scope:
repository `dangelojohn/alfacore`, permissions: Contents: Read. Load
into the cluster:
```bash
kubectl -n alfacore-dev create secret generic alfacore-github-token \
  --from-literal=token=ghp_xxxxx
```
For prod, ExternalSecretsOperator pulls from 1Password — see
`overlays/prod/github-token-external-secret.yaml`.

### P3. No tag has ever been pushed

The entire release pipeline (`build.yml`, `sign.yml`) triggers on
`push: tags: ["v*"]`. Nothing has run end-to-end yet.

## Release procedure

Follow these steps in order. Stop at any failure; do not skip.

### Step 1 — Bring up the dev stack locally and prove the install works

On a Docker-equipped host (Porterly, dev iMac, or anywhere):

```bash
make dev-up
# Wait ~30s for Postgres + Odoo to initialize, then:
open http://localhost:8069
```

In the browser: create database `alfacore_dev`, set master password,
log in as admin, **install `alfa_core_app_api` from Apps** (it depends
on every other AlfaCore module transitively, so this installs all 14).

Watch `make dev-logs` while installing. If any module fails to install,
fix it before continuing. The install must complete with no traceback.

### Step 2 — Run the full test suite

```bash
make test-all-modules
# Or, for just the smoke gate:
docker compose -f docker-compose.dev.yml exec -T odoo \
  odoo-bin -d alfacore_smoke_test -i alfa_core_app_api \
  --test-enable --stop-after-init --test-tags alfacore_smoke \
  --log-level=info
```

All sprint-tagged tests + the smoke tests must pass. If any fail, fix
or quarantine before tagging.

### Step 3 — Load GitHub secrets

Per P2 above (Cosign key + password). Verify with a one-shot test by
pushing a throwaway tag like `v0.0.1-test` and watching `sign.yml`
reach the cosign step in the Actions tab; cancel if it succeeds past
the secret read.

If something is wrong with the Cosign key, you'll see `cosign sign-blob`
exit non-zero at step "Sign every artifact" in `sign.yml`.

### Step 4 — Cut the dev tag

```bash
# Make sure local main matches remote
git fetch origin
git checkout main
git pull --ff-only

# Tag and push
git tag -a v0.1.0-dev -m "AlfaCore v0.1.0-dev — first signed dev cut"
git push origin v0.1.0-dev
```

This triggers, in parallel on GitHub Actions:
- `build.yml` — builds the `addon-loader` container image, pushes
  `ghcr.io/dangelojohn/alfacore-addon-loader:v0.1.0-dev` and `:latest`
- `sign.yml` — packages the modules, Cosign-signs every artifact,
  creates the GitHub Release for `v0.1.0-dev` via `gh release create`,
  uploads tarballs + signatures + `SHA256SUMS` as Release assets

Both should turn green within ~10 minutes. If either fails, investigate
before deploying — a dangling tag without artifacts breaks the
addon-loader at pod start.

### Step 5 — Verify release artifacts are reachable

After both workflows succeed, fetch one of the URLs the
`addon-release-configmap.yaml` points at:

```bash
# Private repo — requires a GitHub PAT (Contents: Read).
TOKEN=$(echo "url=https://github.com" | git credential fill | grep ^password= | cut -d= -f2-)
curl -fIL -H "Authorization: Bearer $TOKEN" -H "Accept: application/octet-stream" \
  https://github.com/dangelojohn/alfacore/releases/download/v0.1.0-dev/alfacore-modules-v0.1.0-dev.tar.gz
curl -fIL -H "Authorization: Bearer $TOKEN" -H "Accept: application/octet-stream" \
  https://github.com/dangelojohn/alfacore/releases/download/v0.1.0-dev/alfacore-modules-v0.1.0-dev.tar.gz.sig
```

Both should return 200 (after redirects to release-asset-storage). If
404, the upload step in `sign.yml` didn't run — re-check Actions logs
for the `gh release create` step output.

### Step 6 — Deploy to dev cluster

On the dev k3d / OrbStack cluster:

```bash
kubectl apply -k deploy/k8s/overlays/dev
kubectl -n alfacore-dev get pods -w
```

Watch the pod come up. The `addon-loader` init-container should:
1. Fetch the tarball from the Release URL
2. Fetch the matching `.sig`
3. Verify the signature against `/mnt/cosign-pubkey/alfacore.cosign.pub`
4. Extract into `/mnt/extra-addons`
5. Exit 0

Then the Odoo container starts. Check `kubectl logs deployment/odoo`
for the boot sequence. Hit the Ingress at `https://alfacore.local`
(or whatever the dev DNS resolves to).

If the addon-loader fails Cosign verification: the signed artifact
and the committed public key disagree. Do not proceed — investigate
key rotation or upload integrity first.

Let dev run for at least 24 hours before promoting. Watch for:
- Odoo OOM-kills (memory budget — adjusted in `2d086c1`, but
  Odoo 19's real footprint may differ from estimates)
- Init-container restart loops (addon-loader signature failures)
- Postgres connection errors (Secret mounted from `postgres-secret.yaml`)

### Step 7 — Cut the prod tag

Only after dev has been clean for 24h+:

```bash
git checkout main
git tag -a v1.0.0 -m "AlfaCore v1.0.0 — first production release"
git push origin v1.0.0
```

Then in the prod overlay, bump pointers:

```bash
# In deploy/k8s/overlays/prod/addon-release-configmap.yaml
# Change v1.0.0 to whatever you just tagged

# In deploy/k8s/overlays/prod/kustomization.yaml
# Update the addon-loader image patch to the same tag

git add deploy/k8s/overlays/prod/
git commit -m "release: pin prod overlay to v1.0.0"
git push origin main
```

Argo CD reconciles within a minute. Verify deploy state in the Argo CD
UI; the addon-loader on prod fetches the signed v1.0.0 artifacts and
boots Odoo.

## Things this checklist does NOT cover

- **Database migrations between versions.** Once v1.0.0 ships, the
  next release needs `migrations/<version>/` scripts for any breaking
  schema change. Not relevant for the first release.
- **Backup before deploy.** Standard Odoo practice — back up the
  filestore PVC and Postgres before any production deploy. Out of
  scope for this checklist; covered separately in OPS-CHECKLIST.
- **Multi-replica HA path.** Currently deferred (Pattern 10). When
  scale demands it: pick one of RWX filestore / S3-backed
  `ir_attachment.location` / Redis session_store, then reintroduce
  `replicas: 2` in the prod overlay.
- **`addon-loader:latest` for dev overlay.** Dev still uses `:latest`
  in the base; prod is pinned per `2d086c1`. If you want dev pinned
  too, mirror the patch into `overlays/dev/kustomization.yaml`.

## Reference

- Forgejo Release API: `POST /api/v1/repos/{owner}/{repo}/releases`,
  `POST /api/v1/repos/{owner}/{repo}/releases/{id}/assets`
- Cosign signing: `cosign sign-blob --key env://COSIGN_PRIVATE_KEY ...`
- Addon-loader source: `addon-loader/{Dockerfile,entrypoint.sh}`
- Architecture corpus: `docs/architecture/` (binding for v1.0.0)
- Twelve Patterns: `CLAUDE.md` (engineering doctrine)
