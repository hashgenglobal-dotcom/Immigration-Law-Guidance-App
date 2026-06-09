-- Immigration Law Guidance App / SourcePath
-- RAG v2 schema migration
-- Purpose:
--   - Add smart-chunk metadata columns
--   - Move legal_chunks.embedding from vector(768) to vector(1024)
--   - Rebuild HNSW index for mxbai-embed-large embeddings
--
-- IMPORTANT:
--   Existing 768-dimensional embeddings cannot be mixed with 1024-dimensional embeddings.
--   This migration intentionally clears existing embedding values during the type change.
--   Re-ingest/re-embed with scripts/smart_chunker.py after applying this migration.

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Smart-chunk semantic metadata
ALTER TABLE legal_chunks ADD COLUMN IF NOT EXISTS visa_types TEXT[];
ALTER TABLE legal_chunks ADD COLUMN IF NOT EXISTS topics TEXT[];
ALTER TABLE legal_chunks ADD COLUMN IF NOT EXISTS forms TEXT[];
ALTER TABLE legal_chunks ADD COLUMN IF NOT EXISTS actions TEXT[];
ALTER TABLE legal_chunks ADD COLUMN IF NOT EXISTS conditions TEXT[];

-- Smart-chunk structural metadata
ALTER TABLE legal_chunks ADD COLUMN IF NOT EXISTS level TEXT;
ALTER TABLE legal_chunks ADD COLUMN IF NOT EXISTS part TEXT;
ALTER TABLE legal_chunks ADD COLUMN IF NOT EXISTS subsection TEXT;
ALTER TABLE legal_chunks ADD COLUMN IF NOT EXISTS paragraph TEXT;

-- Allow longer generated topic labels from the smart chunker.
ALTER TABLE legal_chunks ALTER COLUMN topic TYPE TEXT;
ALTER TABLE legal_chunks ALTER COLUMN subtopic TYPE TEXT;
ALTER TABLE legal_chunks ALTER COLUMN risk_level TYPE TEXT;

-- Drop old 768-dimensional vector index before changing the vector type.
DROP INDEX IF EXISTS idx_legal_chunks_embedding;

-- Existing 768 vectors cannot be cast to 1024 vectors.
-- Clear them during type migration; smart_chunker.py will regenerate 1024 embeddings.
ALTER TABLE legal_chunks
  ALTER COLUMN embedding TYPE vector(1024)
  USING NULL::vector(1024);

-- Update optional query embedding audit column if it exists.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'privacy_safe_answer_logs'
      AND column_name = 'query_embedding'
  ) THEN
    ALTER TABLE privacy_safe_answer_logs
      ALTER COLUMN query_embedding TYPE vector(1024)
      USING NULL::vector(1024);
  END IF;
END $$;

-- Full-text search should include the new metadata.
CREATE OR REPLACE FUNCTION legal_chunks_search_vector_update() RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', COALESCE(NEW.chunk_text, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.plain_language_summary, '')), 'B') ||
    setweight(to_tsvector('english', array_to_string(COALESCE(NEW.visa_types, ARRAY[]::text[]), ' ')), 'B') ||
    setweight(to_tsvector('english', array_to_string(COALESCE(NEW.topics, ARRAY[]::text[]), ' ')), 'B') ||
    setweight(to_tsvector('english', array_to_string(COALESCE(NEW.forms, ARRAY[]::text[]), ' ')), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.citation, '')), 'C') ||
    setweight(to_tsvector('english', COALESCE(NEW.topic, '')), 'D') ||
    setweight(to_tsvector('english', COALESCE(NEW.subtopic, '')), 'D') ||
    setweight(to_tsvector('english', COALESCE(NEW.level, '')), 'D') ||
    setweight(to_tsvector('english', COALESCE(NEW.part, '')), 'D') ||
    setweight(to_tsvector('english', COALESCE(NEW.subsection, '')), 'D') ||
    setweight(to_tsvector('english', COALESCE(NEW.paragraph, '')), 'D');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

-- Metadata indexes for tag-boosted retrieval/debugging.
CREATE INDEX IF NOT EXISTS idx_legal_chunks_visa_types ON legal_chunks USING GIN (visa_types);
CREATE INDEX IF NOT EXISTS idx_legal_chunks_topics ON legal_chunks USING GIN (topics);
CREATE INDEX IF NOT EXISTS idx_legal_chunks_forms ON legal_chunks USING GIN (forms);
CREATE INDEX IF NOT EXISTS idx_legal_chunks_actions ON legal_chunks USING GIN (actions);
CREATE INDEX IF NOT EXISTS idx_legal_chunks_conditions ON legal_chunks USING GIN (conditions);
CREATE INDEX IF NOT EXISTS idx_legal_chunks_level_part ON legal_chunks(level, part);

-- Rebuild vector index for 1024-dimensional mxbai-embed-large vectors.
CREATE INDEX idx_legal_chunks_embedding
  ON legal_chunks USING hnsw (embedding vector_cosine_ops);

COMMIT;
