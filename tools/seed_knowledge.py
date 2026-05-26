#!/usr/bin/env python3
"""
Seed the AlfaCore Knowledge workspace with the architecture corpus.

Reads markdown files from docs/architecture/ (default) and creates Knowledge
articles under the AlfaCore workspace. Idempotent: re-running updates existing
articles rather than duplicating them.

Usage:
    # Default — reads from docs/architecture/ relative to repo root
    python tools/seed_knowledge.py \
        --odoo-url http://localhost:8069 \
        --db alfacore_prod \
        --user admin \
        --password '...'

    # Custom corpus location (e.g., handoff from another machine)
    python tools/seed_knowledge.py \
        --corpus-dir /path/to/handoff \
        --odoo-url http://localhost:8069 \
        --db alfacore_prod \
        --user admin \
        --password '...'
"""

import argparse
import sys
import xmlrpc.client
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_CORPUS_DIR = REPO_ROOT / "docs" / "architecture"

# Read order matters — articles are created in this sequence as siblings under
# the AlfaCore Architecture workspace
CORPUS_FILES = [
    "Alfa-Odoo-Server-Plan-v1.0.md",
    "AlfaCore-Service-Plan-v1.0.md",
    "AlfaCore-JTBD-Gap-Analysis-v1.0.md",
    "AlfaCore-Configurator-JTBD-Gap-Analysis-v1.0.md",
    "AlfaCore-Application-Architecture-Blueprint-v1.0.md",
    "AlfaCore-Decision-Log-v1.0.md",
]

WORKSPACE_NAME = "AlfaCore Architecture"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odoo-url", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=DEFAULT_CORPUS_DIR,
        help=f"Path to corpus markdown files (default: {DEFAULT_CORPUS_DIR})",
    )
    args = parser.parse_args()

    if not args.corpus_dir.exists():
        print(f"ERROR: corpus directory {args.corpus_dir} not found", file=sys.stderr)
        print(
            "If this is a fresh repo, ensure docs/architecture/ is populated with the corpus.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ────────────────────────────────────────────────────────────────
    # Authenticate
    # ────────────────────────────────────────────────────────────────
    common = xmlrpc.client.ServerProxy(f"{args.odoo_url}/xmlrpc/2/common")
    uid = common.authenticate(args.db, args.user, args.password, {})
    if not uid:
        print("ERROR: authentication failed", file=sys.stderr)
        sys.exit(1)

    models = xmlrpc.client.ServerProxy(f"{args.odoo_url}/xmlrpc/2/object")

    # ────────────────────────────────────────────────────────────────
    # Workspace
    # ────────────────────────────────────────────────────────────────
    workspace_ids = models.execute_kw(
        args.db,
        uid,
        args.password,
        "knowledge.article",
        "search",
        [[["name", "=", WORKSPACE_NAME], ["parent_id", "=", False]]],
    )
    if workspace_ids:
        workspace_id = workspace_ids[0]
        print(f"Found existing workspace: {workspace_id}")
    else:
        workspace_id = models.execute_kw(
            args.db,
            uid,
            args.password,
            "knowledge.article",
            "create",
            [{"name": WORKSPACE_NAME, "is_article_visible_by_everyone": False}],
        )
        print(f"Created workspace: {workspace_id}")

    # ────────────────────────────────────────────────────────────────
    # Seed each document
    # ────────────────────────────────────────────────────────────────
    seeded = 0
    skipped = 0
    placeholder = 0

    for fname in CORPUS_FILES:
        fpath = args.corpus_dir / fname
        if not fpath.exists():
            print(f"WARN: {fname} not found in {args.corpus_dir}, skipping")
            skipped += 1
            continue

        content = fpath.read_text()
        title = fname.replace(".md", "").replace("-", " ")

        # Detect placeholder files
        if "PLACEHOLDER" in content[:200]:
            print(
                f"WARN: {fname} is a PLACEHOLDER. Restore the real document before seeding to production."
            )
            placeholder += 1

        existing = models.execute_kw(
            args.db,
            uid,
            args.password,
            "knowledge.article",
            "search",
            [[["name", "=", title], ["parent_id", "=", workspace_id]]],
        )
        if existing:
            models.execute_kw(
                args.db,
                uid,
                args.password,
                "knowledge.article",
                "write",
                [existing, {"body": content}],
            )
            print(f"  Updated: {title}")
        else:
            models.execute_kw(
                args.db,
                uid,
                args.password,
                "knowledge.article",
                "create",
                [
                    {
                        "name": title,
                        "parent_id": workspace_id,
                        "body": content,
                    }
                ],
            )
            print(f"  Created: {title}")
        seeded += 1

    print(f"\nSeeded: {seeded} | Skipped: {skipped} | Placeholders detected: {placeholder}")
    if placeholder:
        print(
            "\nReminder: Replace placeholder files in docs/architecture/ with canonical versions and re-run."
        )


if __name__ == "__main__":
    main()
