#!/usr/bin/env python3
"""
Sync external Python dependencies from all module manifests into root requirements.txt.

Reads __manifest__.py from every alfa_* directory, extracts external_dependencies.python,
deduplicates, and writes to requirements.txt with dev-tooling section preserved.

Run: python tools/sync_deps.py
"""

import ast
from pathlib import Path

ROOT = Path(__file__).parent.parent
DEV_DEPS = [
    "ruff>=0.4.0",
    "pylint>=3.0.0",
    "pylint-odoo>=9.0.0",
]


def extract_python_deps(manifest_path: Path) -> list[str]:
    """Parse a manifest file and return its external_dependencies.python list."""
    try:
        content = manifest_path.read_text()
        # Manifest files are a single dict expression
        tree = ast.parse(content, mode="exec")
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                data = ast.literal_eval(node)
                ext = data.get("external_dependencies", {})
                return ext.get("python", []) or []
    except Exception as e:
        print(f"WARN: could not parse {manifest_path}: {e}")
    return []


def main():
    all_deps: set[str] = set()
    module_dirs = sorted(d for d in ROOT.iterdir() if d.is_dir() and d.name.startswith("alfa_"))

    for mod_dir in module_dirs:
        manifest = mod_dir / "__manifest__.py"
        if manifest.exists():
            for dep in extract_python_deps(manifest):
                all_deps.add(dep)

    out_lines = [
        "# AlfaCore monorepo Python dependencies",
        "# Auto-synced from module manifests via tools/sync_deps.py",
        "# Do not edit manually — re-run sync_deps.py after manifest changes",
        "",
        "# Runtime dependencies (synced from manifests)",
    ]
    for dep in sorted(all_deps):
        # Normalize: ensure a version constraint exists
        if not any(op in dep for op in ["==", ">=", "<=", "~="]):
            dep = f"{dep}>=0"
        out_lines.append(dep)

    out_lines.append("")
    out_lines.append("# Development tools")
    out_lines.extend(DEV_DEPS)

    (ROOT / "requirements.txt").write_text("\n".join(out_lines) + "\n")
    print(f"Wrote requirements.txt with {len(all_deps)} runtime deps + {len(DEV_DEPS)} dev tools")


if __name__ == "__main__":
    main()
