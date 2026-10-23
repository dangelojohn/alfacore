# alfa_core_cuore

**AlfaCore — CUORE bundle import** (Sprint 14)

Offline import of diagnostic bundles (`*.cuore.zip`, schema `cuore.bundle/1.0`) exported by
CUORE, the car-side diagnostic tool. A file is carried from the shop PC to Odoo; there is no
network link, token or REST route between the two.

## What it does

`CUORE -> Import bundle` opens a wizard: upload, validate (errors shown), preview (vehicle
matched by VIN, counts of DTCs, hypotheses and steps), import. Nothing is written before
the person presses Import. `CUORE -> Bundles` lists every bundle with its validation report.

| Bundle kind | Becomes |
|---|---|
| `scan` | one `alfa_core_scanner.scan_session` (source "CUORE wired adapter") with `scan_dtc` rows that keep the UDS status byte and decoded flags, plus freeze-frame, Mode 06, coverage, readiness and requirements JSON |
| `job` | one `alfa_core_diagnosis.report` (state `draft` or `pending_review`, never `reviewed`) with `alfa.cuore.hypothesis` rows that keep CUORE's status and evidence class, proof-of-fix criteria on the report, and one internal `alfa_core_inspection.inspection` per plan whose findings are the mechanic steps |
| both | code findings and TSB cross-reference stored as read-only JSON on `alfa.cuore.bundle` |

## How to import a `.cuore.zip`

1. In CUORE, press **Export for AlfaCore**. The file is written to the CUORE state folder under
   `exports/` as `*.cuore.zip`.
2. Carry the file to the machine you use for Odoo (USB stick or file copy; there is no network link).
3. In Odoo open **CUORE -> Import bundle**. You need the CUORE mechanic group, or advisor or manager.
4. Upload the `.cuore.zip`. The wizard validates it and shows any errors; fix the export, not the file.
5. Check the preview: vehicle matched by VIN, counts of DTCs, hypotheses and steps. Optionally pick the
   service order (its vehicle VIN must equal the bundle's).
6. Press **Import**. Nothing is written before this step. Re-importing the same file is safe: it says
   "already imported" and creates nothing.
7. Review the result under **CUORE -> Bundles**.

The vehicle must already exist in `alfa_fleet`; the importer never creates customers or vehicles.

## Rules the importer keeps

- **Untrusted input.** The vendored `lib/bundle_schema.py` (from CUORE, same author, standard
  library only) checks zip safety, manifest, schema, and every file's SHA-256 and size. The
  hashes detect corruption and truncation, not tampering: bundles are not signed.
- **Idempotent.** `bundle_uuid` is unique. Re-importing the same file says "already imported"
  and creates nothing; the same UUID with different content is refused.
- **All or nothing.** One bundle is written inside one savepoint; a failure rolls back and is
  kept as a `failed` bundle row with the reason.
- **No customers, no vehicles.** The VIN must already exist in `alfa_fleet`. If a service order
  is chosen, its vehicle VIN must equal the bundle's, or the import is refused.
- **Never an inference as a reading.** Evidence class (`reading`, `inference`,
  `outside_literature`, `owner_attested`) is kept exactly as sent. A hypothesis claiming to be
  a reading, or stronger than its weakest support, is rejected. No confidence number is made up
  from CUORE's likelihood labels. A stream that is not a real serial link is stored but flagged
  "NOT a reading from the car". Codes a module merely tracks are counted, not stored as faults.
- **Read-only afterwards.** Imported sessions, DTCs, hypotheses, evidence and bundles reject
  edits and single-row deletes (only the importer, or a manager deleting the whole bundle,
  changes them). A correction is a new scan and a new bundle.
- **Supersession.** A later bundle for the same open scan or job updates the earlier import in
  place (the earlier row becomes `superseded`). A finalized scan or job is never updated, and an
  older export never replaces a newer one.
- `inference_zde = True` on every record the importer creates (AlfaCore has no inheritance code
  for that flag).

## Security

| Group | Can |
|---|---|
| `alfa_core_cuore.group_cuore_mechanic` (implies `alfa_core.group_user`) | run the wizard; read bundles, scans, hypotheses and steps; mark inspection steps |
| `alfa_core.group_advisor` and above | run the wizard; read everything |
| `alfa_core.group_manager` | additionally delete a bundle (removes the records it created, so the file can be imported again) |

The import runs elevated only inside `alfa.cuore.bundle._import` after checking those groups,
and the row records the real importing user. There are no record rules yet (mechanics are not
limited to their own bay); that is a follow-up.

## Honest boundaries (Pattern 10)

Not in this foundation, listed so nobody assumes they exist:

- PIDs / `observations.jsonl` are kept in the attached zip only, not as `scan_pid` rows.
- No `recommendation` rows, `proof_of_fix` model or `quality.check` link, release guard on the
  service order, work order card export, receipt file, station registry, or catalogue (`alfa_tsb`,
  campaign) import. See `docs/integration` in the CUORE repository, spec sections 5.5, 5.6 and 6.6.
- Spec 6.4 rule 8 (reject command-like fields) is not implemented.
- The 3 Odoo tests passed on a throwaway database on 2026-10-22 and the module is installed live. To re-run them:

```bash
odoo-bin -d test_alfacore -i alfa_core_cuore --test-enable --stop-after-init \
         --test-tags=alfacore_sprint14,alfacore_smoke
python -m pytest alfa_core_cuore/tests/test_lib_bundle_schema.py   # no Odoo needed
```

Tests build **synthetic** bundles (`tests/synthetic_bundle.py`, fake VIN, test station). Never
commit a real export: it contains a real VIN.

## Dependencies

```
alfa_core, alfa_fleet, alfa_service, alfa_core_scanner, alfa_core_diagnosis, alfa_core_inspection
```

Configuration parameter `alfa_core_cuore.max_bundle_age_days` (default 14) sets when an old
bundle is flagged with a warning; it never blocks.

## License

LGPL-3 — see root `LICENSE` file.
