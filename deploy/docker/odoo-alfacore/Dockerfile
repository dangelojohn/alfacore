# AlfaCore Odoo runtime — odoo:19 CE with the Python deps the AlfaCore
# modules require but the upstream image doesn't ship.
#
# Why this image exists:
#   - alfa_core_app_api    needs `pyjwt` for JWT auth
#   - alfa_tsb             needs `qdrant-client` (+ numpy + a newer
#                          typing_extensions than Debian ships)
#   - alfa_core_campaign   uses `requests` (already in the base image)
#
# Without this image, every fresh container start requires manual
# `docker exec ... pip install ...` against the running container, and
# the deps are lost on `docker rm` / `docker compose up --force-recreate`.
#
# Build (locally on the QNAP):
#   cd /share/CACHEDEV3_DATA/Container/odoo/addons/deploy/docker/odoo-alfacore
#   docker build -t odoo-alfacore:19 .
#
# Build (via GitHub Actions on tag push):
#   .github/workflows/build.yml's `odoo-image` job pushes
#   ghcr.io/${{ github.repository_owner }}/odoo-alfacore:{tag,latest}
#
# Use:
#   docker-compose.yml:
#     image: ghcr.io/dangelojohn/odoo-alfacore:19   # or :latest
FROM odoo:19

USER root

# typing_extensions: force-upgrade past the Debian-managed copy so
# qdrant-client's resolver doesn't trip on "RECORD file not found"
# when it tries to uninstall the system version.
# Then install AlfaCore's Python deps and verify each imports cleanly.
RUN pip install --break-system-packages --ignore-installed --no-cache-dir typing_extensions \
 && pip install --break-system-packages --no-cache-dir \
        pyjwt \
        numpy \
        qdrant-client \
 && python3 -c "import jwt; import numpy; import qdrant_client; print('AlfaCore Python deps OK')"

USER odoo
