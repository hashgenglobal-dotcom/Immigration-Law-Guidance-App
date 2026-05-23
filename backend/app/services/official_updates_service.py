"""Official Updates — list and detail from PostgreSQL."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from psycopg.rows import dict_row

from app.core.config import Settings
from app.db.connection import connect
from app.services.official_updates_topics import (
    UPDATE_TOPICS,
    parse_topic_filter,
    tag_topics,
    topic_label,
)


class OfficialUpdatesNotReadyError(RuntimeError):
    """Table missing or DB unavailable."""


async def _table_exists(settings: Settings) -> bool:
    async with connect(settings) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'official_updates'
                """
            )
            return await cur.fetchone() is not None


def _row_to_item(row: dict[str, Any]) -> dict[str, Any]:
    bullets = row.get("summary_bullets")
    if isinstance(bullets, str):
        bullets = json.loads(bullets)
    tags = row.get("topic_tags") or []
    if isinstance(tags, str):
        tags = json.loads(tags)
    published = row["published_at"]
    if isinstance(published, datetime):
        published_iso = published.isoformat()
    else:
        published_iso = str(published)
    fetched = row.get("fetched_at")
    fetched_iso = fetched.isoformat() if isinstance(fetched, datetime) else str(fetched)
    return {
        "id": row["id"],
        "publisher": row["publisher"],
        "title": row["title"],
        "official_url": row["official_url"],
        "published_at": published_iso,
        "summary_bullets": list(bullets) if bullets else [],
        "topic_tags": list(tags),
        "topic_labels": [topic_label(t) for t in tags],
        "fetched_at": fetched_iso,
        "has_official_excerpt": bool(row.get("raw_excerpt")),
    }


async def list_topics() -> list[dict[str, str]]:
    return [
        {"id": t.id, "label": t.label, "description": t.description}
        for t in UPDATE_TOPICS
    ]


async def list_updates(
    settings: Settings,
    *,
    topics: str | None = None,
    limit: int = 30,
    offset: int = 0,
) -> dict[str, Any]:
    if not await _table_exists(settings):
        raise OfficialUpdatesNotReadyError(
            "official_updates table not found. Run database/migrations/003-official-updates.sql"
        )

    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    topic_ids = parse_topic_filter(topics)

    async with connect(settings) as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            if topic_ids:
                await cur.execute(
                    """
                    SELECT id, publisher, title, official_url, published_at,
                           summary_bullets, topic_tags, fetched_at, raw_excerpt
                    FROM official_updates
                    WHERE is_published = TRUE
                      AND topic_tags && %s::text[]
                    ORDER BY published_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (topic_ids, limit, offset),
                )
            else:
                await cur.execute(
                    """
                    SELECT id, publisher, title, official_url, published_at,
                           summary_bullets, topic_tags, fetched_at, raw_excerpt
                    FROM official_updates
                    WHERE is_published = TRUE
                    ORDER BY published_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )
            rows = await cur.fetchall()

            if topic_ids:
                await cur.execute(
                    """
                    SELECT COUNT(*) AS n FROM official_updates
                    WHERE is_published = TRUE AND topic_tags && %s::text[]
                    """,
                    (topic_ids,),
                )
            else:
                await cur.execute(
                    "SELECT COUNT(*) AS n FROM official_updates WHERE is_published = TRUE"
                )
            count_row = await cur.fetchone()

    return {
        "status": "ok",
        "privacy_mode": "local-first",
        "items": [_row_to_item(r) for r in rows],
        "count": len(rows),
        "total": int(count_row["n"]) if count_row else 0,
        "limit": limit,
        "offset": offset,
        "topics_filter": topic_ids,
    }


async def get_update(settings: Settings, update_id: int) -> dict[str, Any] | None:
    if not await _table_exists(settings):
        raise OfficialUpdatesNotReadyError(
            "official_updates table not found. Run database/migrations/003-official-updates.sql"
        )

    async with connect(settings) as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, publisher, title, official_url, published_at,
                       summary_bullets, topic_tags, fetched_at, raw_excerpt
                FROM official_updates
                WHERE id = %s AND is_published = TRUE
                """,
                (update_id,),
            )
            row = await cur.fetchone()

    if not row:
        return None
    item = _row_to_item(row)
    item["raw_excerpt"] = row.get("raw_excerpt")
    return item


async def upsert_feed_item(
    settings: Settings,
    *,
    publisher: str,
    external_id: str,
    title: str,
    official_url: str,
    published_at: datetime,
    raw_excerpt: str | None,
    summary_bullets: list[str],
    topic_tags: list[str],
    content_hash: str,
    summary_model: str | None,
) -> bool:
    """Insert or update; returns True if inserted new row."""
    tags = topic_tags or tag_topics(title, raw_excerpt)
    params = (
        publisher,
        external_id,
        title,
        official_url,
        published_at,
        raw_excerpt,
        json.dumps(summary_bullets),
        tags,
        content_hash,
        summary_model,
    )
    async with connect(settings) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO official_updates (
                    publisher, external_id, title, official_url, published_at,
                    raw_excerpt, summary_bullets, topic_tags, content_hash,
                    summary_model, fetched_at, is_published
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, NOW(), TRUE
                )
                ON CONFLICT (publisher, external_id) DO NOTHING
                RETURNING id
                """,
                params,
            )
            inserted = await cur.fetchone() is not None
            if not inserted:
                await cur.execute(
                    """
                    UPDATE official_updates SET
                        title = %s, official_url = %s, published_at = %s,
                        raw_excerpt = %s, summary_bullets = %s::jsonb,
                        topic_tags = %s, content_hash = %s,
                        summary_model = %s, fetched_at = NOW()
                    WHERE publisher = %s AND external_id = %s
                    """,
                    (
                        title,
                        official_url,
                        published_at,
                        raw_excerpt,
                        json.dumps(summary_bullets),
                        tags,
                        content_hash,
                        summary_model,
                        publisher,
                        external_id,
                    ),
                )
        await conn.commit()
    return inserted
