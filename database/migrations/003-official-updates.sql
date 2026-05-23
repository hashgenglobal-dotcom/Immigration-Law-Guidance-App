-- Official Updates: government announcement feed (separate from legal_chunks RAG corpus).
-- Run after 001-initial-schema.sql. Safe to re-run (IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS official_updates (
    id              BIGSERIAL PRIMARY KEY,
    publisher       TEXT NOT NULL,
    external_id     TEXT NOT NULL,
    title           TEXT NOT NULL,
    official_url    TEXT NOT NULL,
    published_at    TIMESTAMPTZ NOT NULL,
    raw_excerpt     TEXT,
    summary_bullets JSONB NOT NULL DEFAULT '[]'::jsonb,
    topic_tags      TEXT[] NOT NULL DEFAULT '{}',
    content_hash    TEXT NOT NULL,
    summary_model   TEXT,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_published    BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT official_updates_publisher_external_id_key UNIQUE (publisher, external_id)
);

CREATE INDEX IF NOT EXISTS idx_official_updates_published_at
    ON official_updates (published_at DESC)
    WHERE is_published = TRUE;

CREATE INDEX IF NOT EXISTS idx_official_updates_topic_tags
    ON official_updates USING GIN (topic_tags);

COMMENT ON TABLE official_updates IS
    'USCIS/DHS/Federal Register announcements with plain-language summaries. Not mixed into legal_chunks retrieval by default.';
