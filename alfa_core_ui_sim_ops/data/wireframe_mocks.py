# SPDX-License-Identifier: LGPL-3.0-only
"""Mockup data for ops wireframes — used when ?mockup=1 is on the URL.

Keep mock dictionaries here so they're auditable in one file. Each top-level
key corresponds to a controller method's surface name.

When stakeholders ask "are these visuals fake or live?", point them at this
file: anything in here is fake-by-construction.
"""

from datetime import datetime


def _now():
    return datetime.now()


TECHNICIAN_TABLET = {
    "current_job": {
        "name": "AC-2026-0438",
        "customer_name": "John D'Angelo",
        "vehicle_label": "2018 Stelvio Ti · ZASFAKBN3J7C12345",
        "mileage_km": 89247,
        "bay": "Bay 2 (4-post)",
        "service_state": "in_progress",
        "operations": [
            {"name": "Coil swap diagnostic", "state": "complete", "duration_min": 18},
            {"name": "Replace coil PN 55214664 cyl 1", "state": "in_progress", "duration_min": 12},
            {"name": "Clear DTCs, road test", "state": "pending", "duration_min": 15},
        ],
        "parts_picked": [
            {"part_number": "55214664", "name": "Ignition coil", "qty": 1, "vendor": "MOPAR"},
        ],
        "dtcs_active": ["P0301", "P0507"],
    }
}

ADVISOR_COCKPIT = {
    "kpis": {
        "open_orders": 12,
        "awaiting_parts": 3,
        "ready_for_pickup": 2,
        "today_revenue_cad": 8245,
    },
    "queue": [
        {
            "name": "AC-2026-0438",
            "customer": "John D'Angelo",
            "state": "in_progress",
            "vehicle": "Stelvio Ti",
            "tech": "M. Conte",
            "eta": "14:30",
        },
        {
            "name": "AC-2026-0441",
            "customer": "M. Bianchi",
            "state": "parts_ready",
            "vehicle": "Giulia QV",
            "tech": "—",
            "eta": "tomorrow AM",
        },
        {
            "name": "AC-2026-0445",
            "customer": "G. Marchetti",
            "state": "scheduled",
            "vehicle": "Stelvio",
            "tech": "—",
            "eta": "Thu 10:00",
        },
        {
            "name": "AC-2026-0448",
            "customer": "L. Conte",
            "state": "awaiting_review",
            "vehicle": "Tonale",
            "tech": "A. Rossi",
            "eta": "—",
        },
    ],
    "alerts": [
        {"severity": "warn", "text": "AC-2026-0438: Cyl-1 coil swap complete, awaiting road test"},
        {"severity": "info", "text": "Bay 1 lift due for monthly safety inspection"},
    ],
}

PRO_REVIEW_QUEUE = {
    "reports": [
        {
            "name": "AC-DX-2026-000001",
            "vehicle": "2018 Stelvio Ti",
            "customer": "John D'Angelo",
            "severity": "warn",
            "confidence": 0.78,
            "age_hours": 2,
            "primary_dtc": "P0301",
            "state": "pending_review",
        },
        {
            "name": "AC-DX-2026-000002",
            "vehicle": "2020 Giulia QV",
            "customer": "M. Bianchi",
            "severity": "severe",
            "confidence": 0.84,
            "age_hours": 5,
            "primary_dtc": "P200A",
            "state": "pending_review",
        },
        {
            "name": "AC-DX-2026-000003",
            "vehicle": "2019 Stelvio",
            "customer": "G. Marchetti",
            "severity": "safety_critical",
            "confidence": 0.92,
            "age_hours": 0.5,
            "primary_dtc": "C0561",
            "state": "pending_review",
        },
    ],
}

LOANER_GANTT = {
    "vehicles": [
        {"name": "Loaner Stelvio Ti #1", "plate": "CDXJ 101", "tier": "premium"},
        {"name": "Loaner Stelvio Ti #2", "plate": "CDXJ 102", "tier": "premium"},
        {"name": "Loaner Giulia Sprint #1", "plate": "CDXJ 103", "tier": "premium"},
        {"name": "Loaner Giulia QV", "plate": "CDXJ 104", "tier": "pro"},
        {"name": "Loaner Tonale", "plate": "CDXJ 105", "tier": "basic_plus"},
    ],
    "allocations": [
        {
            "vehicle_idx": 0,
            "customer": "John D'Angelo",
            "day_start": 0,
            "day_span": 3,
            "state": "active",
        },
        {
            "vehicle_idx": 1,
            "customer": "M. Bianchi",
            "day_start": 1,
            "day_span": 2,
            "state": "scheduled",
        },
        {
            "vehicle_idx": 3,
            "customer": "(Pro pool)",
            "day_start": 4,
            "day_span": 2,
            "state": "scheduled",
        },
    ],
    "day_labels": ["Mon 12", "Tue 13", "Wed 14", "Thu 15", "Fri 16", "Sat 17", "Sun 18"],
}
