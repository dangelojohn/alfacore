#!/usr/bin/env python3
"""Validate every __manifest__.py: required keys, version prefix, license."""

import ast
import pathlib
import sys

REQUIRED_KEYS = {"name", "version", "depends", "license", "installable"}


def main() -> int:
    errors = []
    manifests = list(pathlib.Path(".").glob("alfa_*/__manifest__.py"))
    for mf in manifests:
        try:
            data = ast.literal_eval(mf.read_text())
        except Exception as e:
            errors.append(f"{mf}: parse error: {e}")
            continue
        missing = REQUIRED_KEYS - set(data.keys())
        if missing:
            errors.append(f"{mf}: missing required keys {missing}")
        if data.get("license") != "LGPL-3":
            errors.append(f"{mf}: license must be 'LGPL-3', got {data.get('license')!r}")
        version = data.get("version", "")
        if not version.startswith("19."):
            errors.append(f"{mf}: version must start with '19.', got {version!r}")
    if errors:
        for e in errors:
            print("FAIL:", e)
        return 1
    print(f"All {len(manifests)} manifests valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
