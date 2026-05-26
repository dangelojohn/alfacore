# addon-loader

Init-container that fetches the AlfaCore module tarball from a release URL,
verifies its Cosign signature against the committed public key, and unpacks
it into a shared volume that Odoo reads as its `addons_path`.

## Why this exists

The AlfaCore Deployment runs the stock `ghcr.io/odoo/odoo:19.0` image. The
custom modules live in a separate `extra-addons` volume that must be
populated before Odoo starts. In dev that volume is hand-managed; in prod
it must be populated from a **verified signed artifact** — otherwise the
GitOps chain is broken (anyone with cluster write access could substitute
unsigned modules).

This init-container closes that gap. It runs once per pod start, before
the Odoo container starts, and is fail-closed: any failure to fetch,
verify, or extract aborts the pod.

## Image lifecycle

The image is built and pushed on every `v*` tag of the AlfaCore repo by
`.github/workflows/build.yml`. The resulting image is itself Cosign-signed
by `.github/workflows/sign.yml` so that you can `cosign verify` the
loader image before it ever runs (defense in depth — even the verifier is
verified).

The image tag matches the AlfaCore release tag: a deployment of AlfaCore
v1.0.0 uses `addon-loader:v1.0.0`, which fetches and verifies the
`alfacore-modules-v1.0.0.tar.gz` artifact.

## Required environment

| Variable | Purpose |
|---|---|
| `ADDON_TARBALL_URL`    | Where to fetch the signed `.tar.gz` |
| `ADDON_SIGNATURE_URL`  | Where to fetch the matching `.sig` |

Both URLs typically point at Forgejo Release assets:
```
https://github.com/dangelojohn/alfacore/releases/download/${TAG}/alfacore-modules-${TAG}.tar.gz
https://github.com/dangelojohn/alfacore/releases/download/${TAG}/alfacore-modules-${TAG}.tar.gz.sig
```

## Required mounts

| Mount | Source | Purpose |
|---|---|---|
| `/mnt/cosign-pubkey/alfacore.cosign.pub` | `ConfigMap: alfacore-cosign-pubkey` | Verification public key — committed to the repo at `alfacore.cosign.pub` and loaded into K8s as a ConfigMap by Kustomize |
| `/mnt/extra-addons/` | `emptyDir` shared with the Odoo container | Destination for unpacked modules |
| `/tmp` | implicit | Scratch space for the downloaded tarball + signature |

## Failure modes

The script exits non-zero on:

| Exit | Cause |
|---|---|
| 1    | Public key not mounted, or destination volume not present (config error) |
| 2    | Signature verification failed (security event — investigate before any retry) |
| any other | curl failure (network, 404, etc.) |

A signature failure is a **security event**, not a transient error. Argo CD
will retry the pod, but if the artifact is genuinely tampered, every retry
will fail until either the artifact is replaced with a correctly-signed
version or the public key is rotated (and committed). Do not work around
this by disabling verification.

## Local testing

```bash
# Build the image
cd addon-loader/
docker build -t alfacore-addon-loader:dev .

# Run it locally against a test artifact (e.g. a release in your fork)
docker run --rm \
  -v $(pwd)/../alfacore.cosign.pub:/mnt/cosign-pubkey/alfacore.cosign.pub:ro \
  -v $(pwd)/test-output:/mnt/extra-addons \
  -e ADDON_TARBALL_URL=https://example.tld/alfacore-modules-v0.0.1-test.tar.gz \
  -e ADDON_SIGNATURE_URL=https://example.tld/alfacore-modules-v0.0.1-test.tar.gz.sig \
  alfacore-addon-loader:dev
```
