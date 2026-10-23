# SPDX-License-Identifier: LGPL-3.0-only
"""Pure-Python reading of a CUORE bundle that has already passed ``bundle_schema``.

No Odoo import: everything here takes plain dicts and returns plain dicts, so the
mapping decisions (which DTC rows exist, which evidence class a row carries, which
steps become inspection lines) can be tested without an Odoo install.

The bundle is untrusted input. Nothing here evaluates, executes or extracts to disk.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from typing import Any

# Weakest-wins ranking, exactly as CUORE states it in job.json ("ranking"):
# reading > inference > owner_attested > outside_literature.
EVIDENCE_RANK = {"reading": 3, "inference": 2, "owner_attested": 1, "outside_literature": 0}
EVIDENCE_CLASSES = tuple(EVIDENCE_RANK)

HYPOTHESIS_STATUSES = ("open", "supported", "confirmed", "refuted")
DTC_CODE = re.compile(r"^[PBCU][0-9A-F]{4}$")
OBD_KIND_TO_STATUS = {"stored": "active", "pending": "pending", "permanent": "permanent"}

#: Compressed archive size cap (the validator caps the expanded size separately).
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024

_ISO = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d+)?(Z|[+-]\d{2}:\d{2})$",
)


def weakest(classes: list[str]) -> str:
    """The weakest evidence class of ``classes`` (``inference`` when empty)."""
    known = [c for c in classes if c in EVIDENCE_RANK]
    return min(known, key=EVIDENCE_RANK.__getitem__) if known else "inference"


def parse_aware_iso(value: Any) -> datetime | None:
    """Offset-aware ISO 8601 -> naive UTC datetime (what Odoo stores); None if unusable."""
    if not isinstance(value, str):
        return None
    m = _ISO.match(value.strip())
    if not m:
        return None
    base, frac, off = m.groups()
    digits = (frac or ".")[1:7].ljust(6, "0") if frac else ""
    off = "+00:00" if off == "Z" else off
    try:
        dt = datetime.fromisoformat(f"{base}{'.' + digits if digits else ''}{off}")
    except ValueError:
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None)  # noqa: UP017 (3.10 tooling)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bundle(data: bytes) -> tuple[dict[str, Any], dict[str, Any]]:
    """(manifest, parts) of a bundle. ``parts`` maps ``scan.json`` etc. to parsed JSON.

    Call only after ``bundle_schema.validate_bundle`` returned no errors.
    ``observations.jsonl`` is not parsed (it stays in the stored zip).
    """
    parts: dict[str, Any] = {}
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        for entry in manifest.get("files") or []:
            path = entry["path"]
            if path.endswith(".json"):
                parts[path] = json.loads(zf.read(path).decode("utf-8"))
    return manifest, parts


def peek_manifest(data: bytes) -> dict[str, Any]:
    """Best-effort manifest for an invalid bundle (to show the person what it claimed)."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
    except (zipfile.BadZipFile, KeyError, ValueError, OSError):
        return {}
    return manifest if isinstance(manifest, dict) else {}


# --- semantic checks the JSON schema cannot express ---------------------------------


def semantic_errors(manifest: dict[str, Any], parts: dict[str, Any]) -> tuple[list[str], list[str]]:
    """(errors, warnings) from rules on the data (spec 6.4 rules 5 and 7)."""
    errors: list[str] = []
    warnings: list[str] = []
    kind = manifest.get("kind")
    need = {"scan": "scan.json", "job": "job.json"}.get(kind)
    if need and need not in parts:
        errors.append(f"a {kind} bundle must contain {need}")
    job = (parts.get("job.json") or {}).get("job") or {}
    for h in job.get("hypotheses") or []:
        hid = h.get("id")
        cls = h.get("evidence_class")
        if cls == "reading":
            errors.append(
                f"hypothesis {hid}: a hypothesis is never a reading (a code or a test result "
                "supports it; the hypothesis itself is an inference at best)"
            )
            continue
        supports = ["inference"] + [r.get("evidence_class") for r in h.get("evidence_for") or []]
        if h.get("attested_resolved"):
            supports.append("owner_attested")
        ceiling = weakest(supports)
        if EVIDENCE_RANK.get(cls, 0) > EVIDENCE_RANK[ceiling]:
            errors.append(
                f"hypothesis {hid}: evidence_class {cls!r} is stronger than its weakest "
                f"support ({ceiling!r}); the importer never raises a class"
            )
        if h.get("status") not in HYPOTHESIS_STATUSES:
            errors.append(f"hypothesis {hid}: unknown status {h.get('status')!r}")
        if h.get("status") == "confirmed" and not h.get("deleted"):
            tests = [r for r in h.get("evidence_for") or [] if r.get("result") in ("pass", "fail")]
            if not tests:
                warnings.append(
                    f"hypothesis {hid} is 'confirmed' in CUORE without a recorded pass/fail test "
                    "(CUORE is the authority; recorded as sent, flagged here)"
                )
            if h.get("evidence_against"):
                warnings.append(
                    f"hypothesis {hid} is 'confirmed' with evidence recorded against it"
                )
    scan = parts.get("scan.json") or {}
    if scan and not scan.get("from_car"):
        warnings.append(
            "the scan is not from a real serial link: its rows are stored but never shown as readings"
        )
    return errors, warnings


# --- flattening into rows the Odoo layer can create ---------------------------------


def dtc_rows(parts: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Rows for ``alfa_core_scanner.scan_dtc`` and counters.

    Only active and history codes become rows. A code a module merely tracks (the
    19 02 reply lists hundreds) or one with only the readiness bit is counted in
    ``not_run`` and is never a fault row (spec 5.2).
    """
    rows: list[dict[str, Any]] = []
    counts = {
        "active": 0,
        "history": 0,
        "pending": 0,
        "permanent": 0,
        "not_run": 0,
        "skipped_unknown_kind": 0,
    }
    dtcs = parts.get("dtcs.json") or {}
    for mod in dtcs.get("module_dtcs") or []:
        for r in mod.get("dtcs") or []:
            state = r.get("state")
            if state not in ("active", "history"):
                counts["not_run"] += 1
                continue
            counts[state] += 1
            raw = r.get("raw")
            rows.append(
                {
                    "dtc_code": r.get("base_code") or str(r.get("code") or "").partition("-")[0],
                    "dtc_status": state,
                    "module_source": mod.get("ecu") or "",
                    "bus": mod.get("bus") or "",
                    "failure_type_byte": r.get("failure_type_byte") or "",
                    "status_byte": r.get("status") if isinstance(r.get("status"), int) else 0,
                    "flags": r.get("flags") if isinstance(r.get("flags"), dict) else {},
                    "source_service": "uds_19_02",
                    "raw_payload": raw
                    if isinstance(raw, str)
                    else (json.dumps(raw) if raw else ""),
                    "from_car": bool(mod.get("from_car")),
                }
            )
    for grp in dtcs.get("obd_dtcs") or []:
        status = OBD_KIND_TO_STATUS.get(str(grp.get("dtc_kind") or ""))
        service = {"stored": "obd_03", "pending": "obd_07", "permanent": "obd_0a"}.get(
            str(grp.get("dtc_kind") or ""), ""
        )
        by_code: dict[str, str] = {}
        if isinstance(grp.get("by_ecu"), dict):
            for ecu, codes in grp["by_ecu"].items():
                for c in codes if isinstance(codes, list) else []:
                    by_code[str(c.get("code") if isinstance(c, dict) else c).partition("-")[0]] = (
                        ecu
                    )
        for item in grp.get("dtcs") or []:
            code = str(item.get("code") if isinstance(item, dict) else item).partition("-")[0]
            if status is None:
                counts["skipped_unknown_kind"] += 1
                continue
            counts[status] += 1
            rows.append(
                {
                    "dtc_code": code,
                    "dtc_status": status,
                    "module_source": by_code.get(code, ""),
                    "bus": grp.get("bus") or "",
                    "failure_type_byte": "",
                    "status_byte": 0,
                    "flags": {},
                    "source_service": service,
                    "raw_payload": "",
                    "from_car": bool(grp.get("from_car")),
                }
            )
    return rows, counts


def step_key(hypothesis_id: str, title: str, source: str) -> str:
    """Stable identity of a plan step. ``n`` is order only: it renumbers (spec 5.4)."""
    return sha256_hex(f"{hypothesis_id}|{title}|{source}".encode())[:12]


def plan_rows(parts: dict[str, Any]) -> list[dict[str, Any]]:
    """One entry per mechanic plan that has steps: {hypothesis_id, rationale, steps: [...]}."""
    out: list[dict[str, Any]] = []
    for plan in (parts.get("mechanic_steps.json") or {}).get("plans") or []:
        hid = str(plan.get("hypothesis_id") or "")
        steps = []
        seen: dict[str, int] = {}
        for s in plan.get("steps") or []:
            title = str(s.get("title") or "")
            source = str(s.get("source") or "")
            key = step_key(hid, title, source)
            seen[key] = seen.get(key, 0) + 1
            if seen[key] > 1:  # identical title+source twice in one plan: keep keys unique
                key = f"{key}-{seen[key]}"
            steps.append(
                {
                    "step_key": key,
                    "step_order": int(s.get("n") or 0),
                    "name": title,
                    "note": str(s.get("detail") or ""),
                    "step_kind": str(s.get("kind") or ""),
                    "step_source": source,
                    "step_tools": ", ".join(str(t) for t in s.get("tools") or []),
                    "step_bulletins": ", ".join(
                        str(b.get("number") if isinstance(b, dict) else b)
                        for b in s.get("bulletins") or []
                    ),
                    "step_done": bool(s.get("done")),
                    "step_done_ref": str(s.get("done_ref") or ""),
                    "evidence_class": s.get("evidence_class"),
                }
            )
        if steps:
            out.append(
                {
                    "hypothesis_id": hid,
                    "rationale": str(plan.get("rationale") or ""),
                    "steps": steps,
                }
            )
    return out


def hypothesis_rows(parts: dict[str, Any]) -> list[dict[str, Any]]:
    """Hypotheses with their evidence references, class and status exactly as sent."""
    job = (parts.get("job.json") or {}).get("job") or {}
    rows = []
    for h in job.get("hypotheses") or []:
        evidence = []
        for side in ("for", "against"):
            for ref in h.get(f"evidence_{side}") or []:
                evidence.append(
                    {
                        "side": side,
                        "kind": str(ref.get("kind") or ""),
                        "ref_id": str(ref.get("id") or ""),
                        "label": str(ref.get("label") or ""),
                        "result": str(ref.get("result") or ""),
                        "evidence_class": ref.get("evidence_class"),
                    }
                )
        rows.append(
            {
                "hyp_id": str(h.get("id") or ""),
                "text": str(h.get("text") or ""),
                "system": str(h.get("system") or ""),
                "status": h.get("status"),
                "likelihood": h.get("likelihood") or "",
                "next_test": str(h.get("next_test") or ""),
                "codes": ", ".join(str(c) for c in h.get("codes") or []),
                "safety": bool(h.get("safety")),
                "attested_resolved": bool(h.get("attested_resolved")),
                "deleted": bool(h.get("deleted")),
                "evidence_class": h.get("evidence_class"),
                "evidence_class_basis": str(h.get("evidence_class_basis") or ""),
                "audit": h.get("audit") or [],
                "evidence": evidence,
            }
        )
    return rows


def summarise(manifest: dict[str, Any], parts: dict[str, Any]) -> dict[str, Any]:
    """Counts shown in the preview (spec 6.3 step 3)."""
    dtcs, counts = dtc_rows(parts)
    hyps = hypothesis_rows(parts)
    plans = plan_rows(parts)
    return {
        "dtc_rows": len(dtcs),
        "dtc_active": counts["active"],
        "dtc_history": counts["history"],
        "dtc_not_run": counts["not_run"],
        "hypotheses": sum(1 for h in hyps if not h["deleted"]),
        "hypotheses_deleted": sum(1 for h in hyps if h["deleted"]),
        "plans": len(plans),
        "steps": sum(len(p["steps"]) for p in plans),
        "by_class": {
            c: sum(1 for h in hyps if h["evidence_class"] == c and not h["deleted"])
            for c in EVIDENCE_CLASSES
        },
    }


def template_technical_summary(manifest: dict[str, Any], parts: dict[str, Any]) -> str:
    """Template-generated (not LLM) technician text; every statement carries its class."""
    job = (parts.get("job.json") or {}).get("job") or {}
    lines = [
        f"Imported from CUORE bundle {manifest.get('bundle_uuid')} (station "
        f"{manifest.get('station_id')}, job {job.get('id')}).",
        "Hypothesis statuses and evidence classes are CUORE's, read-only here. "
        "No numeric confidence is computed or shown.",
        f"Complaint (as typed in CUORE): {job.get('complaint') or '(none)'}",
        "",
    ]
    for h in hypothesis_rows(parts):
        if h["deleted"]:
            continue
        lines.append(
            f"[{str(h['evidence_class']).upper()}] {h['text']} -- status: {h['status']}"
            + (f", likelihood: {h['likelihood']}" if h["likelihood"] else "")
            + (", SAFETY" if h["safety"] else "")
        )
        if h["next_test"]:
            lines.append(f"    next test: {h['next_test']}")
    return "\n".join(lines)


__all__ = [
    "EVIDENCE_CLASSES",
    "EVIDENCE_RANK",
    "MAX_ARCHIVE_BYTES",
    "dtc_rows",
    "hypothesis_rows",
    "parse_aware_iso",
    "peek_manifest",
    "plan_rows",
    "read_bundle",
    "semantic_errors",
    "sha256_hex",
    "step_key",
    "summarise",
    "template_technical_summary",
    "weakest",
]
