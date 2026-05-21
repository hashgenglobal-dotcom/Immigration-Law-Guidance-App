"""Read-only admin summaries for source/dataset health (POST-09)."""

from __future__ import annotations

from psycopg.rows import dict_row

from app.core.config import Settings
from app.db.connection import connect


async def list_dataset_summary(settings: Settings) -> dict:
    async with connect(settings) as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, version_name, status, activated_at
                FROM dataset_versions
                ORDER BY activated_at DESC NULLS LAST, id DESC
                LIMIT 50
                """
            )
            datasets = await cur.fetchall()
            await cur.execute(
                "SELECT COUNT(*) AS n FROM legal_chunks WHERE is_active = TRUE"
            )
            chunk_row = await cur.fetchone()
    total_active_chunks = int(chunk_row["n"]) if chunk_row else 0
    return {
        "datasets": [dict(r) for r in datasets],
        "total_active_chunks": total_active_chunks,
    }


async def source_registry_summary(settings: Settings) -> list[dict]:
    async with connect(settings) as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, source_name, source_type, official_base_url, is_active
                FROM source_registry
                ORDER BY source_name
                """
            )
            rows = await cur.fetchall()
    return [dict(r) for r in rows]
