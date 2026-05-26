#!/usr/bin/env bash
# AlfaCore addon-loader entrypoint.
#
# Fail-closed: if any step fails, the script exits non-zero, the init-container
# fails, the Odoo pod doesn't start. There is no fallback to unsigned addons.
#
# Required environment:
#   ADDON_TARBALL_URL    — where to fetch the .tar.gz (a GitHub Release asset)
#   ADDON_SIGNATURE_URL  — where to fetch the matching .sig
#   GITHUB_TOKEN         — PAT or fine-grained token with read access to the
#                          dangelojohn/alfacore private repo (mounted from
#                          the alfacore-github-token Secret). Without this,
#                          fetches from github.com release assets 404 because
#                          the source repo is private.
#
# Required mounts:
#   /mnt/cosign-pubkey/alfacore.cosign.pub  — verification public key (ConfigMap)
#   /mnt/extra-addons/                       — destination volume (shared with Odoo)
#   /tmp                                     — scratch space

set -euo pipefail

# --- Sanity checks ---------------------------------------------------------
: "${ADDON_TARBALL_URL:?ADDON_TARBALL_URL must be set}"
: "${ADDON_SIGNATURE_URL:?ADDON_SIGNATURE_URL must be set}"
: "${GITHUB_TOKEN:?GITHUB_TOKEN must be set (private-repo Releases are auth-gated)}"

PUBKEY="/mnt/cosign-pubkey/alfacore.cosign.pub"
DEST="/mnt/extra-addons"

if [[ ! -f "$PUBKEY" ]]; then
    echo "FATAL: public key not mounted at $PUBKEY"
    exit 1
fi

if [[ ! -d "$DEST" ]]; then
    echo "FATAL: destination volume not mounted at $DEST"
    exit 1
fi

# --- Fetch ----------------------------------------------------------------
TARBALL="/tmp/alfacore-modules.tar.gz"
SIGNATURE="/tmp/alfacore-modules.tar.gz.sig"

# GitHub Release assets on a private repo require Authorization + the
# api.github.com/octet-stream content type to redirect to the actual blob.
# The Authorization header survives the redirect because we explicitly
# include --header in every retry attempt.
GH_AUTH_HEADER="Authorization: Bearer $GITHUB_TOKEN"
GH_ACCEPT_HEADER="Accept: application/octet-stream"

echo "[1/4] Fetching tarball from $ADDON_TARBALL_URL"
curl --silent --show-error --fail --location \
     --max-time 120 --retry 3 --retry-delay 5 \
     --header "$GH_AUTH_HEADER" --header "$GH_ACCEPT_HEADER" \
     --output "$TARBALL" "$ADDON_TARBALL_URL"

echo "[2/4] Fetching signature from $ADDON_SIGNATURE_URL"
curl --silent --show-error --fail --location \
     --max-time 30 --retry 3 --retry-delay 5 \
     --header "$GH_AUTH_HEADER" --header "$GH_ACCEPT_HEADER" \
     --output "$SIGNATURE" "$ADDON_SIGNATURE_URL"

# --- Verify ---------------------------------------------------------------
echo "[3/4] Verifying Cosign signature against $PUBKEY"
if ! cosign verify-blob \
        --key "$PUBKEY" \
        --signature "$SIGNATURE" \
        "$TARBALL"; then
    echo "FATAL: signature verification failed. Refusing to extract."
    echo "       The published artifact does not match the committed public key."
    echo "       Either the artifact was tampered with, or the signing key was"
    echo "       rotated without a matching pubkey commit. Do not proceed."
    exit 2
fi
echo "       Signature OK."

# --- Extract --------------------------------------------------------------
echo "[4/4] Extracting verified tarball into $DEST"
# Clear the destination first — any cruft from previous deploys would
# poison the addons_path. The PVC is intentionally an emptyDir below.
rm -rf "$DEST"/*

tar -xzf "$TARBALL" -C "$DEST"

# Show what we unpacked
echo "       Extracted module count: $(find "$DEST" -maxdepth 1 -name 'alfa_*' -type d | wc -l)"
echo
echo "addon-loader: complete. Handing off to Odoo container."
