# AlfaCore Deployment

Argo CD-managed GitOps deployment to Kubernetes. Two environments out of the
box: `dev` (John's iMac k3d/OrbStack cluster) and `prod` (CloudClusters managed
K8s). Both pull from the same Forgejo repo, the same `main` branch — the
overlay handles env-specific config.

## Topology

```
Forgejo repo (source of truth)
  ├─ alfacore.cosign.pub                   public verification key (committed)
  ├─ addon-loader/                         init-container source
  ├─ .github/workflows/                   build, sign, validate, test
  └─ deploy/
      ├─ k8s/base/                         Kustomize base
      ├─ k8s/overlays/dev/                 k3d overlay
      ├─ k8s/overlays/prod/                CloudClusters overlay
      └─ argocd/application.yaml           Argo CD Applications

Forgejo Releases (signed artifact storage)
  └─ vN.M.K/
      ├─ alfacore-modules-vN.M.K.tar.gz
      └─ alfacore-modules-vN.M.K.tar.gz.sig

Argo CD (in cluster, watching the repo)
  ├─ alfacore-dev   → kustomize build overlays/dev | kubectl apply
  └─ alfacore-prod  → kustomize build overlays/prod | kubectl apply

Kubernetes pod startup
  ├─ initContainer: addon-loader
  │     fetch tarball + sig from Forgejo Release
  │     cosign verify-blob against /mnt/cosign-pubkey/alfacore.cosign.pub
  │     extract verified tarball into /mnt/extra-addons
  └─ container: odoo
        starts with addons_path = /mnt/extra-addons
```

## The GitOps loop is closed

Every link is now signed-and-verified end-to-end:

1. **Source**: Git commits on `main` are review-gated by the validate /
   lint / test workflows. No code reaches main without passing the
   syntax + manifest + XML-ID + Odoo test sweep.
2. **Build**: tag-triggered `build.yml` packages every module + a full
   bundle tarball.
3. **Sign**: `sign.yml` Cosign-signs every tarball with the private key
   stored in the `ALFACORE_COSIGN_KEY` secret. It also self-verifies
   against the committed public key (catches key rotation drift).
4. **Publish**: signed artifacts + `.sig` files land as Forgejo Release
   assets, addressable by their tag.
5. **Deploy**: Argo CD reconciles the cluster state from the
   `deploy/k8s/overlays/{env}` Kustomize overlay.
6. **Verify**: at pod startup, the `addon-loader` init-container fetches
   the release tarball, verifies the Cosign signature against the
   ConfigMap-mounted public key, and refuses to extract if verification
   fails. The Odoo container can't start with tampered or unsigned addons.

## Bootstrap

### One-time prerequisites

**Both clusters**:
- `bash tools/setup_cosign.sh` to generate the keypair (do this once)
- The resulting `alfacore.cosign.pub` is committed to the repo root
- `ALFACORE_COSIGN_KEY` and `ALFACORE_COSIGN_PASSWORD` are added as Forgejo
  repo secrets (also stored offline in 1Password)
- `GITHUB_TOKEN (automatic in Actions)` added as a repo secret for the addon-loader
  image push

**Dev cluster** (John's iMac, k3d on OrbStack):
- k3d cluster running
- Argo CD installed
- Forgejo repo + container registry reachable from inside the cluster
  (Tailscale Funnel or in-cluster Forgejo)

**Prod cluster** (CloudClusters):
- Cluster provisioned per CloudClusters docs
- Argo CD installed
- External Secrets Operator installed
- 1Password Connect ClusterSecretStore configured as `realpartners-1password`
- cert-manager installed with `letsencrypt-prod` ClusterIssuer

### Install the Application manifests

```bash
kubectl apply -n argocd -f deploy/argocd/application.yaml

# Watch the rollout:
argocd app get alfacore-prod --refresh
argocd app sync alfacore-prod
```

### Cut a release

```bash
git tag v1.0.0
git push origin v1.0.0
# build.yml + sign.yml run automatically. After they complete:
# - alfacore-modules-v1.0.0.tar.gz lives in Forgejo Releases
# - alfacore-modules-v1.0.0.tar.gz.sig lives alongside
# - ghcr.io/dangelojohn/alfacore-addon-loader:v1.0.0 is published

# Promote to prod:
# Edit deploy/k8s/overlays/prod/addon-release-configmap.yaml to point at v1.0.0
# Commit on main, push, PR, merge.
# Argo CD reconciles. Init-container fetches + verifies + extracts. Odoo
# rolls with the new modules.
```

## Per-environment specifics

### Dev (`overlays/dev`)
- Single Odoo replica (`workers = 0` for breakpoint debugging)
- In-cluster Postgres secret (plain `Secret`, dev-only password)
- Ingress host: `alfacore.local` (add to `/etc/hosts` for browser access)
- Resource limits: 2 CPU / 2 GiB — leaves headroom on the i9 iMac
- Tracks dev release tags (e.g. `v0.1.0-dev`)

### Prod (`overlays/prod`)
- 2 Odoo replicas with rolling update (zero-downtime deploys)
- Postgres credentials sourced from 1Password via External Secrets
- Real TLS via cert-manager + Let's Encrypt
- Ingress host: `alfacore.realpartners.tld`
- Resource limits: 4 CPU / 8 GiB per Odoo pod
- Pinned to a tagged release (e.g. `v1.0.0`)

## Operational notes

- **Backup**: prod cron should `pg_dump` the Postgres StatefulSet PVC daily
  to off-cluster storage (S3, B2, or QNAP via Tailscale). A `CronJob` overlay
  is recommended; not in this layout yet.
- **Migrations**: Odoo handles module upgrades via `-u <module>`. After a
  tagged release, run a one-shot Job: `odoo-bin -d <db> -u <module>
  --stop-after-init`. Argo CD will not run this for you; it's app-level
  schema management.
- **Worker scaling**: bump `replicas` in `overlays/prod/kustomization.yaml`
  and the workers count in `odoo.conf`. Stickiness on `session_id` cookie
  is set at the ingress level — verify Traefik annotations if you scale
  beyond 2 replicas.
- **PIPEDA**: the `dbfilter = ^alfacore.*` line in `odoo.conf` is critical.
  Without it, a misconfigured proxy can leak DB listing. Verify on every
  prod deploy.
- **Key rotation**: documented inline in `deploy/k8s/base/cosign-pubkey-configmap.yaml`.
  Five steps, all reviewable on PR.
