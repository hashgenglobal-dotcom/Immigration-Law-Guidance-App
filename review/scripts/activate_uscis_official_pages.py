#!/usr/bin/env python3
"""Activate the latest uscis-official-pages dataset after embeddings are complete.

Sets dataset status=active, is_active=TRUE on its chunks, and updates search_vector
via existing DB triggers or leaves to embed script post-step.

Usage:
    uv run --project backend python review/scripts/activate_uscis_official_pages.py --dry-run
    uv run --project backend python review/scripts/activate_uscis_official_pages.py --yes
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import psycopg
except ImportError:
    sys.exit(1)


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url and Path("backend/.env").exists():
        for line in Path("backend/.env").read_text().splitlines():
            if line.strip().startswith("DATABASE_URL="):
                url = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not url:
        sys.exit("DATABASE_URL required")
    return re.sub(r"^postgresql\+[a-zA-Z0-9_]+://", "postgresql://", url)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-version-name", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    if not args.dry_run and not args.yes:
        print("Use --dry-run or --yes")
        return 1

    with psycopg.connect(_db_url()) as conn:
        with conn.cursor() as cur:
            if args.dataset_version_name:
                name = args.dataset_version_name
            else:
                cur.execute(
                    """
                    SELECT version_name FROM dataset_versions
                    WHERE version_name LIKE 'uscis-official-pages-%'
                    ORDER BY version_name DESC LIMIT 1
                    """
                )
                row = cur.fetchone()
                if not row:
                    print("No uscis-official-pages dataset found")
                    return 1
                name = row[0]

            cur.execute(
                "SELECT id, status FROM dataset_versions WHERE version_name = %s",
                (name,),
            )
            dv = cur.fetchone()
            if not dv:
                print(f"Dataset not found: {name}")
                return 1
            dv_id, status = dv

            cur.execute(
                """
                SELECT COUNT(*), COUNT(*) FILTER (WHERE embedding IS NOT NULL)
                FROM legal_chunks WHERE dataset_version_id = %s
                """,
                (dv_id,),
            )
            total, embedded = cur.fetchone()
            print(f"Dataset {name} (id={dv_id}) status={status}")
            print(f"  chunks={total} embedded={embedded}")
            if embedded < total:
                print("  WARN: not all chunks embedded; activation may hurt retrieval quality")

            if args.dry_run:
                print("DRY-RUN: would set active + is_active=TRUE")
                return 0

            cur.execute(
                """
                UPDATE dataset_versions SET status = 'active', activated_at = NOW()
                WHERE id = %s
                """,
                (dv_id,),
            )
            cur.execute(
                """
                UPDATE legal_chunks SET is_active = TRUE
                WHERE dataset_version_id = %s AND embedding IS NOT NULL
                """,
                (dv_id,),
            )
            activated = cur.rowcount
        conn.commit()
        print(f"Activated {activated} chunks for {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
