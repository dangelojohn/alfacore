# SPDX-License-Identifier: LGPL-3.0-only
"""Builds SYNTHETIC ``*.cuore.zip`` bundles for tests (schema ``cuore.bundle/1.0``).

Pure standard library, no Odoo import, so the same fixtures serve the pure-Python
validator test and the Odoo TransactionCase tests. Everything here is made up: the VIN
is fake (ISO 3779 shape only, not a real vehicle) and the station id is a test slug.
Never copy a real exported bundle into this repo: it contains a real VIN.
"""

from __future__ import annotations

import hashlib
import io
import json
import uuid
import zipfile
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

SYNTH_VIN = "ZARSYNTH1J7000001"  # fake: valid ISO 3779 shape, no I/O/Q, not a real car
OTHER_VIN = "ZARSYNTH1J7000002"
STATION = "test-station-01"
JOB_ID = "synthjob0001"
SCAN_ID = "SCAN_2601011200"


def _obs(kind: str, data: dict[str, Any], *, from_car: bool = True) -> dict[str, Any]:
    return {
        "at": "2026-01-01T12:00:00",
        "at_iso": "2026-01-01T12:00:00+00:00",
        "tz_assumed": False,
        "kind": kind,
        "stream": "serial:test" if from_car else "replay:test",
        "from_car": from_car,
        "data": data,
    }


def _flags(status: int) -> dict[str, bool]:
    names = (
        "test_failed",
        "test_failed_this_cycle",
        "pending",
        "confirmed",
        "not_completed_since_clear",
        "failed_since_clear",
        "not_completed_this_cycle",
        "warning_indicator",
    )
    return {n: bool(status & (1 << i)) for i, n in enumerate(names)}


def default_parts(kind: str, vin: str, *, from_car: bool = True) -> dict[str, Any]:
    """Part files (parsed) for a scan or job bundle; callers may mutate before packing."""
    parts: dict[str, Any] = {}
    if kind == "scan":
        rows = [
            ("P0456-00", 0x09),  # active (test failed + confirmed)
            ("P0442-00", 0x20),  # history
            ("P0455-00", 0x10),  # tracked only: never a fault row
            ("P0440-00", 0x40),  # readiness bit only: never a fault row
        ]
        parts["scan.json"] = {
            "scan_id": SCAN_ID,
            "vin": vin,
            "status": "complete",
            "from_car": from_car,
            "streams": ["serial:test" if from_car else "replay:test"],
            "window": {
                "start_iso": "2026-01-01T11:55:00+00:00",
                "end_iso": "2026-01-01T12:10:00+00:00",
            },
            "cable": "test-cable",
            "buses_attempted": ["can_c"],
            "guided": {"status": "done", "segments": [{"n": 1, "bus": "can_c", "status": "ok"}]},
            "coverage": [
                {
                    "bus": "can_c",
                    "module": "ECM",
                    "category": "answered",
                    "active": 1,
                    "history": 1,
                },
                {"bus": "can_c", "module": "TCM", "category": "silent", "why": "no answer"},
            ],
            "steps": [],
            "counts": {"active": 1, "history": 1, "not_run": 2},
        }
        parts["dtcs.json"] = {
            "module_dtcs": [
                {
                    "ecu": "ECM",
                    "bus": "can_c",
                    "from_car": from_car,
                    "dtcs": [
                        {
                            "code": code,
                            "base_code": code.partition("-")[0],
                            "failure_type_byte": "00",
                            "status": st,
                            "flags": _flags(st),
                            "state": (
                                "active"
                                if st & 0x0D
                                else "history"
                                if st & 0x20
                                else "readiness_only"
                                if st == 0x40
                                else "tracked"
                            ),
                            "raw": "00",
                        }
                        for code, st in rows
                    ],
                }
            ],
            "obd_dtcs": [
                {"dtc_kind": "stored", "from_car": from_car, "bus": "can_c", "dtcs": ["P0456"]}
            ],
        }
        parts["freeze_frames.json"] = {
            "mode02": [
                _obs("freeze_frame", {"dtc": "P0456", "pids": {"0C": 850}}, from_car=from_car)
            ],
            "dtc_detail": [],
        }
        parts["mode06.json"] = {
            "records": [_obs("mode06", {"mid": "3C", "tid": "01", "value": 5}, from_car=from_car)]
        }
        parts["readiness.json"] = {
            "records": [_obs("readiness", {"evap_verdict": "not_run"}, from_car=from_car)]
        }
        parts["evap_bundle.json"] = {"present": False, "records": []}
        parts["scan_requirements.json"] = {
            "scan_id": SCAN_ID,
            "met": ["dtc_stored"],
            "gaps": [],
            "needs_mechanic": [],
            "not_applicable": [],
            "captured": 3,
            "required": 3,
        }
    else:
        parts["job.json"] = {
            "job": {
                "id": JOB_ID,
                "vin": vin,
                "status": "open",
                "complaint": "synthetic complaint: intermittent warning light",
                "technician": "test technician",
                "outcome": None,
                "verification": {"codes_returned": [], "readiness_at": None, "verdict": None},
                "hypotheses": [
                    {
                        "id": "hyp00001",
                        "text": "Synthetic inference: purge valve sticks open",
                        "system": "evap",
                        "status": "open",
                        "likelihood": "med",
                        "next_test": "smoke test the line",
                        "codes": ["P0456"],
                        "safety": False,
                        "attested_resolved": False,
                        "deleted": False,
                        "evidence_class": "inference",
                        "evidence_class_basis": "weakest of text and supports",
                        "evidence_for": [
                            {
                                "kind": "code",
                                "id": "c1",
                                "label": "P0456 active",
                                "result": "",
                                "evidence_class": "reading",
                            }
                        ],
                        "evidence_against": [],
                        "audit": [{"action": "created", "at_iso": "2026-01-01T12:00:00+00:00"}],
                    },
                    {
                        "id": "hyp00002",
                        "text": "Synthetic owner statement: leak found by hand",
                        "system": "evap",
                        "status": "supported",
                        "likelihood": "",
                        "next_test": "",
                        "codes": [],
                        "safety": True,
                        "attested_resolved": False,
                        "deleted": False,
                        "evidence_class": "owner_attested",
                        "evidence_class_basis": "weakest of text and supports",
                        "evidence_for": [
                            {
                                "kind": "test",
                                "id": "t1",
                                "label": "smoke test fail",
                                "result": "fail",
                                "evidence_class": "owner_attested",
                            }
                        ],
                        "evidence_against": [],
                        "audit": [],
                    },
                    {
                        "id": "hyp00003",
                        "text": "Synthetic deleted hypothesis",
                        "system": "electrical",
                        "status": "refuted",
                        "likelihood": "",
                        "next_test": "",
                        "codes": [],
                        "safety": False,
                        "attested_resolved": False,
                        "deleted": True,
                        "evidence_class": "inference",
                        "evidence_class_basis": "",
                        "evidence_for": [],
                        "evidence_against": [],
                        "audit": [],
                    },
                ],
                "actions": [
                    {
                        "id": "act00001",
                        "kind": "test",
                        "at": "2026-01-01T12:05:00",
                        "event_date": None,
                        "effective_date": "2026-01-01T12:05:00",
                        "evidence_class": "owner_attested",
                    }
                ],
            },
            "evidence_class_rules": {
                "ranking": "reading > inference > owner_attested > outside_literature"
            },
        }
        parts["mechanic_steps.json"] = {
            "plans": [
                {
                    "hypothesis_id": "hyp00001",
                    "rationale": "synthetic rationale",
                    "steps": [
                        {
                            "n": 0,
                            "title": "Never clear codes",
                            "detail": "Do not clear any DTC until the hypothesis is resolved.",
                            "kind": "precondition",
                            "source": "project rule: never clear codes",
                            "done": False,
                            "done_ref": "",
                            "evidence_class": "inference",
                            "tools": [],
                            "bulletins": [],
                        },
                        {
                            "n": 1,
                            "title": "Inspect purge valve",
                            "detail": "Look at the valve and hose.",
                            "kind": "inspect",
                            "source": "OUTSIDE LITERATURE, not a reading from this car: synthetic note",
                            "done": True,
                            "done_ref": "act00001",
                            "evidence_class": "outside_literature",
                            "tools": ["hand vacuum pump"],
                            "bulletins": [{"number": "00-000-00"}],
                        },
                    ],
                },
                {"hypothesis_id": "hyp00002", "steps": []},
            ]
        }
        parts["proof_of_fix.json"] = {
            "present": False,
            "job_id": JOB_ID,
            "criteria": [
                {
                    "code": "P0456-00",
                    "module": "ECM",
                    "proof": "Absent over three reads across 21 days, status bytes read before any clear.",
                    "evidence_class": "inference",
                }
            ],
            "verification": {"codes_returned": [], "readiness_at": None, "verdict": None},
            "outcome": None,
        }
    parts["tsb_xref.json"] = {
        "vin": vin,
        "available": True,
        "bulletins": [
            {
                "id": "b1",
                "number": "00-000-00",
                "title": "Synthetic bulletin",
                "relations": [{"relation": "candidate", "reason": "synthetic"}],
                "evidence_class": "outside_literature",
            }
        ],
    }
    parts["code_findings.json"] = {
        "codes": ["P0456"],
        "findings": [
            {
                "code": "P0456-00",
                "meaning": "EVAP small leak (synthetic)",
                "evidence": {
                    "readings": ["synthetic reading"],
                    "inference": ["synthetic inference"],
                    "outside_literature": [],
                    "owner_attested": [],
                },
            }
        ],
    }
    return parts


def _dump(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, indent=1).encode("utf-8")


def build_bundle(
    kind: str = "scan",
    *,
    vin: str = SYNTH_VIN,
    source_id: str | None = None,
    station_id: str = STATION,
    created_at: datetime | None = None,
    finalized: bool = True,
    from_car: bool = True,
    bundle_uuid: str | None = None,
    mutate_parts: Callable[[dict[str, Any]], None] | None = None,
    mutate_manifest: Callable[[dict[str, Any]], None] | None = None,
    extra_files: dict[str, bytes] | None = None,
    salt: str = "",
) -> bytes:
    """A valid bundle (zip bytes). ``mutate_*`` run before hashing, so the result is still
    internally consistent; use :func:`tamper_member` to break the hashes on purpose."""
    parts = default_parts(kind, vin, from_car=from_car)
    if mutate_parts:
        mutate_parts(parts)
    source_id = source_id or (SCAN_ID if kind == "scan" else JOB_ID)
    created = created_at or datetime.now(timezone.utc)  # noqa: UP017
    members = {name: _dump(data) for name, data in parts.items()}
    members["observations.jsonl"] = (
        json.dumps({"kind": "seed", "n": 1}) + "\n" if kind == "scan" else ""
    ).encode("utf-8")
    if kind != "scan":
        members.pop("observations.jsonl")
    for name, raw in (extra_files or {}).items():
        members[name] = raw
    files = [
        {"path": n, "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}
        for n, b in sorted(members.items())
    ]
    manifest: dict[str, Any] = {
        "schema": "cuore.bundle/1.0",
        "bundle_uuid": bundle_uuid
        or str(uuid.uuid5(uuid.NAMESPACE_URL, f"{station_id}|{kind}|{source_id}|{salt}|{created}")),
        "kind": kind,
        "source_id": source_id,
        "station_id": station_id,
        "created_at": created.isoformat(timespec="seconds"),
        "tz": "UTC",
        "cuore_version": "0.0.0-test",
        "vehicle": {
            "vin": vin,
            "identities": [
                {"ecu": "ECM", "bus": "can_c", "fields": {"F190": {"name": "VIN", "ascii": vin}}}
            ],
        },
        "files": files,
        "contains": sorted(parts),
        "warnings": [] if finalized else ["job is open: a later bundle may supersede this one"],
        "finalized": finalized,
    }
    if mutate_manifest:
        mutate_manifest(manifest)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", _dump(manifest))
        for name, raw in members.items():
            zf.writestr(name, raw)
    return buf.getvalue()


def tamper_member(bundle: bytes, member: str, replace: bytes | None = None) -> bytes:
    """Rewrite one member without touching the manifest, so its SHA-256 no longer matches."""
    out = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(bundle)) as src,
        zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst,
    ):
        for info in src.infolist():
            raw = src.read(info.filename)
            if info.filename == member:
                raw = replace if replace is not None else raw + b" "
            dst.writestr(info.filename, raw)
    return out.getvalue()


def old_created_at(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)  # noqa: UP017


def later_created_at(minutes: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)  # noqa: UP017
