#!/usr/bin/env python3
"""Verify every file listed in __manifest__.py's data/demo arrays exists on disk."""

import ast
import pathlib
import sys


def main() -> int:
    errors = []
    for mf in pathlib.Path(".").glob("alfa_*/__manifest__.py"):
        try:
            data = ast.literal_eval(mf.read_text())
        except Exception as e:
            errors.append(f"{mf}: parse error: {e}")
            continue
        module_dir = mf.parent
        for rel in data.get("data", []) + data.get("demo", []):
            if not (module_dir / rel).exists():
                errors.append(f"{mf}: references missing file {rel!r}")
    if errors:
        for e in errors:
            print("FAIL:", e)
        return 1
    print("All manifest-referenced files exist on disk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
