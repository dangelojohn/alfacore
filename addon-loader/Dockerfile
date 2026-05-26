# AlfaCore addon-loader — pulls + Cosign-verifies + extracts the signed
# module tarball before Odoo starts.
#
# This is an init-container, not a long-running service. It runs once per
# pod start, exits when extraction completes (or fails verification and
# refuses to extract — fail-closed by design).

FROM gcr.io/projectsigstore/cosign:v2.4.1 AS cosign

FROM alpine:3.20
RUN apk add --no-cache curl tar bash ca-certificates && \
    update-ca-certificates

COPY --from=cosign /ko-app/cosign /usr/local/bin/cosign

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Verification key is mounted at /mnt/cosign-pubkey/alfacore.cosign.pub
# Output addons unpack into /mnt/extra-addons (shared with the Odoo container)
# Source URL is provided via env: ADDON_TARBALL_URL, ADDON_SIGNATURE_URL

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
