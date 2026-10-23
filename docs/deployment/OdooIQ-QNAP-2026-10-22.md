# AlfaCore — OdooIQ QNAP Live Deployment Record

**Date:** 2026-10-22
**Subject:** State of the live AlfaCore instance and the install of `alfa_core_cuore` (Sprint 14)
**Author:** REAL Partners Ltd. / OdooIQ
**License:** LGPL-3.0-only

This is a dated record of what was running and what was done. It contains no passwords, database
credentials or other secrets, and none should ever be added to it.

---

## 1. Host and containers

| Item | Value |
|---|---|
| Host | OdooIQ QNAP TS-x51, QTS 5.2.9, `192.168.68.108` |
| URLs | `http://192.168.68.108:9080` and `https://192.168.68.108:9443` (self-signed certificate) |
| Front door | container `alfacore-caddy`, which proxies to `odoo:8069` |
| Network | `alfacore-net` |

| Container | Image / role |
|---|---|
| `alfacore-odoo` | `odoo-alfacore:19` (Odoo `19.0-20260504`) |
| `alfacore-postgres` | PostgreSQL; database `alfacore` |
| `alfacore-caddy` | Caddy reverse proxy |

The same QNAP also hosts Forgejo (repository `qnap/alfacore`) and about seven other Odoo instances behind
the same Caddy (ports 9444-9452).

### The system-docker.sock gotcha

QNAP runs a **second Docker daemon** for Container Station. The AlfaCore containers live on that one.
The default socket shows only old, stopped containers, which looks like "nothing is running".
Always address the right daemon:

```bash
docker -H unix:///var/run/system-docker.sock ps
```

## 2. Volumes and `odoo.conf` highlights

Data is on Vol 1 (`Vol_System`, `CACHEDEV3`) under `/share/Container/odoo/`:

| Path | Holds |
|---|---|
| `addons/` | custom modules (the `alfa_*` folders) |
| `config/` | `odoo.conf` |
| `odoo-data/` | filestore |
| `logs/` | Odoo logs |

`odoo.conf` highlights (values that matter operationally; no credentials listed here):

- `dbfilter = ^alfacore$`
- `workers = 3`
- `list_db = False`

## 3. Module state before the install

- 16 `alfa_*` modules installed.
- `alfa_core_loaner_sign` uninstalled (the opt-in e-signature module).
- `alfa_tsb` present in the addons folder but **not registered** in Odoo. It needs
  **Apps > Update Apps List** before it can be installed (see OPS-CHECKLIST Phase H).

## 4. Installing `alfa_core_cuore`: test first, then install

Rule followed: never install a new module straight into the live database. Test on a throwaway database,
take a backup, then install.

### 4.1 Throwaway test

1. Start a one-off `odoo-alfacore:19` container on `alfacore-net`.
2. Mount the live `odoo.conf` read-only.
3. Put the branch's addons in `/share/Container/alfacore-cuore-test`.
4. Run with `-d alfacore_cuore_test --test-enable --stop-after-init --workers=0`.
5. Result: the 3 Odoo tests pass.
6. Clean up: `dropdb` the test database (retry if sessions linger), then remove the test folder.

### 4.2 Backup

Pre-install dump, kept in the OdooIQ backup share:

`OdooIQ-Backups/alfacore_before_cuore_20261022-210645.dump`

### 4.3 Live install

1. Copy the module into `/share/Container/odoo/addons`.
2. Run a one-off `odoo-alfacore:19` container on `alfacore-net` with
   `-i alfa_core_cuore --stop-after-init` against the live database `alfacore`.
3. No restart was needed: registry signalling reloaded the workers.

Outcome: `alfa_core_cuore` is **installed live on `alfacore` as of 2026-10-22**.

## 5. The `.po` gotcha

The Odoo 19 i18n loader needs a `#. module: <name>` comment on **every** `.po` entry. Without it the
install crashes (`odoo/tools/translate.py`, around line 854). The first version of the module's `.po`
files lacked these comments; fixed in commit `452c10d`. Any new module with `i18n/*.po` files must carry
the comment on each entry.

## 6. Live logins (names only)

| Login | State |
|---|---|
| `admin` | uid 2, active, last sign-in 2026-06-09 |
| `demo` | uid 5, active record, never signed in |

Passwords are stored hashed and cannot be read back. They are reset through the Odoo shell **when the
owner asks**. A reset script was prepared but has **not** been run: it is blocked pending the owner's
explicit OK. Never write a password in this repository, the wiki or a ticket.

## 7. Security rotation note

On the shared QNAP host, the database passwords of **other** Odoo containers were visible in a `ps`
listing. No values are recorded here. Rotation is recommended (OPS-CHECKLIST Phase H), and container
passwords should be supplied by an environment file or secret rather than on the command line, so they do
not appear in a process listing.

## 8. Related

- CUORE integration: the wiki page `CUORE-Integration`, and the CUORE repository
  (`https://github.com/dangelojohn/CUORE`, `docs/integration/`).
- Module README: `alfa_core_cuore/README.md`.
- Branch history: `1f7ac55` (feature), `452c10d` (`.po` fix), merged to `main` as `a7dce7b`.
- Still open: a pilot with one real service order moved by file (CUORE export, then AlfaCore import).
