#!/usr/bin/env python3
"""Cross-reference every ref="..." in XML against defined XML IDs.

Handles three classes of references:
- Same-module bare refs: ref="my_record_id"
- Cross-module qualified refs: ref="other_module.record_id"
- Odoo core module refs: ref="base.view_partner_form" (trusted via depends)
- Auto-generated model IDs: ref="model_alfa_core_campaign_nhtsa_client"

Catches the cheap, high-frequency bugs: typos in XML IDs, model name mismatches
in demo data, references to records that were renamed but not updated in callers.
"""

import pathlib
import re
import sys
from xml.etree import ElementTree as ET

# Odoo core modules whose XML IDs we trust at install time (declared in
# __manifest__.py depends, resolved by Odoo's dependency loader).
ODOO_CORE_MODULES = {
    "base",
    "web",
    "mail",
    "portal",
    "website",
    "sale",
    "sale_management",
    "sale_subscription",
    "account",
    "purchase",
    "stock",
    "hr",
    "sign",
    "product",
    "uom",
    "calendar",
    "contacts",
    "resource",
    "barcodes",
    "digest",
    "bus",
    "report",
}

# \b at the front prevents accidental matches inside attribute names that
# end in -ref (`t-attf-href`, `aria-ref`, etc.). Without it, the substring
# `ref="…"` inside `href="…"` triggers a false positive.
REF_PATTERN = re.compile(r'\bref=["\']([^"\'\s]+)["\']')
MODEL_NAME_PATTERN = re.compile(r'_name\s*=\s*["\']([\w.]+)["\']')


def collect_defined_ids() -> set:
    """Walk the repo collecting every XML ID that's defined somewhere."""
    defined = set()

    # Odoo auto-generates model_<snake_case_name> XML IDs for every Python model.
    for py in pathlib.Path(".").glob("alfa_*/**/*.py"):
        for match in MODEL_NAME_PATTERN.finditer(py.read_text()):
            model_name = match.group(1)
            auto_id = "model_" + model_name.replace(".", "_")
            module = py.parts[0]
            defined.add(f"{module}.{auto_id}")
            defined.add(auto_id)

    # XML records, templates, and menuitems define IDs explicitly.
    for xml in pathlib.Path(".").glob("alfa_*/**/*.xml"):
        module = xml.parts[0]
        try:
            tree = ET.parse(xml)
        except ET.ParseError:
            continue
        for elem in tree.iter():
            if elem.tag in ("record", "template", "menuitem"):
                xid = elem.get("id")
                if xid:
                    defined.add(f"{module}.{xid}")
                    defined.add(xid)

    return defined


def main() -> int:
    defined = collect_defined_ids()
    errors = []

    for xml in pathlib.Path(".").glob("alfa_*/**/*.xml"):
        text = xml.read_text()
        for match in REF_PATTERN.finditer(text):
            ref = match.group(1)
            # Skip refs into Odoo core modules — they resolve at install time
            if "." in ref and ref.split(".", 1)[0] in ODOO_CORE_MODULES:
                continue
            if "." not in ref:
                module = xml.parts[0]
                if f"{module}.{ref}" not in defined and ref not in defined:
                    errors.append(f"{xml}: ref={ref!r} not defined")
            else:
                if ref not in defined:
                    errors.append(f"{xml}: ref={ref!r} not defined anywhere")

    if errors:
        for e in errors[:50]:
            print("FAIL:", e)
        if len(errors) > 50:
            print(f"... and {len(errors) - 50} more")
        return 1
    print(f"All XML refs cross-resolve ({len(defined) // 2} IDs defined).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
