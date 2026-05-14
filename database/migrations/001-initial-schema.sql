-- Immigration Law Guidance App - Database Schema
-- Version: 1.0
-- Created: 2026-05-14
-- PostgreSQL 17 + pgvector 0.8.2

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- For fuzzy text matching
CREATE EXTENSION IF NOT EXISTS btree_gin; -- For composite index support

-- ============================================================================
-- SOURCE REGISTRY
-- Tracks official legal sources (USCIS, eCFR, INA, BIA, Federal Register)
-- ============================================================================
CREATE TABLE source_registry (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL, -- 'regulation', 'statute', 'policy', 'case_law', 'form'
    publisher VARCHAR(255) NOT NULL, -- 'USCIS', 'DOJ', 'GPO', 'Federal Register'
    base_url TEXT,
    access_method VARCHAR(50), -- 'api', 'bulk_xml', 'scraping', 'manual'
    update_frequency VARCHAR(50), -- 'daily', 'weekly', 'monthly', 'on_demand'
    is_official BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_source_registry_name ON source_registry(source_name);
CREATE INDEX idx_source_registry_type ON source_registry(source_type);

-- ============================================================================
-- RAW DOCUMENTS
-- Stores original fetched content (audit trail, version tracking)
-- ============================================================================
CREATE TABLE raw_documents (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES source_registry(id) ON DELETE CASCADE,
    external_id VARCHAR(255), -- Source's own identifier (e.g., CFR section number)
    title TEXT NOT NULL,
    citation VARCHAR(255), -- Official citation (e.g., "8 CFR § 208.7")
    official_url TEXT,
    raw_format VARCHAR(50), -- 'html', 'xml', 'json', 'text', 'pdf'
    raw_content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL, -- SHA256 for change detection
    fetched_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    effective_date DATE,
    version_date DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_raw_documents_source ON raw_documents(source_id);
CREATE INDEX idx_raw_documents_external_id ON raw_documents(external_id);
CREATE INDEX idx_raw_documents_citation ON raw_documents(citation);
CREATE INDEX idx_raw_documents_hash ON raw_documents(content_hash);
CREATE INDEX idx_raw_documents_fetched ON raw_documents(fetched_at);

-- ============================================================================
-- LEGAL DOCUMENTS
-- Cleaned document-level information (parsed from raw)
-- ============================================================================
CREATE TABLE legal_documents (
    id SERIAL PRIMARY KEY,
    raw_document_id INTEGER NOT NULL REFERENCES raw_documents(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    citation VARCHAR(255),
    jurisdiction VARCHAR(100) DEFAULT 'United States',
    publisher VARCHAR(255) NOT NULL,
    official_url TEXT,
    effective_date DATE,
    version_date DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_legal_documents_citation ON legal_documents(citation);
CREATE INDEX idx_legal_documents_source_type ON legal_documents(source_type);

-- ============================================================================
-- LEGAL SECTIONS
-- Specific legal sections within documents (e.g., 8 CFR § 208.7(a))
-- ============================================================================
CREATE TABLE legal_sections (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES legal_documents(id) ON DELETE CASCADE,
    section_number VARCHAR(100), -- e.g., "208.7", "208.7(a)"
    section_title TEXT,
    citation VARCHAR(255) NOT NULL, -- Full citation: "8 CFR § 208.7(a)"
    official_text TEXT NOT NULL, -- Original legal text
    cleaned_text TEXT, -- Normalized for processing
    topic VARCHAR(100), -- e.g., 'asylum', 'adjustment_of_status'
    subtopic VARCHAR(100), -- e.g., 'employment_authorization', 'filing_deadline'
    audience VARCHAR(50), -- 'general', 'attorney', 'student', 'employer'
    official_url TEXT,
    effective_date DATE,
    version_date DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_legal_sections_citation ON legal_sections(citation);
CREATE INDEX idx_legal_sections_topic ON legal_sections(topic);
CREATE INDEX idx_legal_sections_subtopic ON legal_sections(subtopic);
CREATE INDEX idx_legal_sections_document ON legal_sections(document_id);

-- ============================================================================
-- LEGAL CHUNKS
-- Retrieval-ready chunks with embeddings (main table for user queries)
-- ============================================================================
CREATE TABLE legal_chunks (
    id SERIAL PRIMARY KEY,
    section_id INTEGER NOT NULL REFERENCES legal_sections(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL, -- Order within section (0, 1, 2, ...)
    chunk_text TEXT NOT NULL,
    plain_language_summary TEXT, -- Simplified explanation
    citation VARCHAR(255) NOT NULL,
    topic VARCHAR(100) NOT NULL,
    subtopic VARCHAR(100),
    risk_level VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    official_url TEXT,
    embedding vector(768), -- pgvector: 768 dimensions (nomic-embed-text)
    -- Alternative: vector(1536) for OpenAI text-embedding-3-small
    search_vector tsvector, -- PostgreSQL full-text search
    dataset_version_id INTEGER, -- Links to dataset_versions
    is_active BOOLEAN DEFAULT FALSE, -- Only active chunks are retrieved
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for retrieval
CREATE INDEX idx_legal_chunks_embedding ON legal_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_legal_chunks_search_vector ON legal_chunks USING GIN (search_vector);
CREATE INDEX idx_legal_chunks_topic_subtopic ON legal_chunks(topic, subtopic);
CREATE INDEX idx_legal_chunks_active ON legal_chunks(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_legal_chunks_dataset ON legal_chunks(dataset_version_id);
CREATE INDEX idx_legal_chunks_citation ON legal_chunks(citation);

-- Full-text search index trigger
CREATE OR REPLACE FUNCTION legal_chunks_search_vector_update() RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', COALESCE(NEW.chunk_text, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.plain_language_summary, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.citation, '')), 'C') ||
    setweight(to_tsvector('english', COALESCE(NEW.topic, '')), 'D') ||
    setweight(to_tsvector('english', COALESCE(NEW.subtopic, '')), 'D');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER legal_chunks_search_vector_trigger
  BEFORE INSERT OR UPDATE ON legal_chunks
  FOR EACH ROW EXECUTE FUNCTION legal_chunks_search_vector_update();

-- ============================================================================
-- SCENARIO GUIDES
-- Practical user-friendly guides for common situations
-- ============================================================================
CREATE TABLE scenario_guides (
    id SERIAL PRIMARY KEY,
    scenario_title TEXT NOT NULL,
    user_situation TEXT NOT NULL, -- "ICE came to my door", "I overstayed my visa"
    plain_language_guidance TEXT NOT NULL,
    what_to_do TEXT[], -- Array of action items
    what_not_to_do TEXT[], -- Array of warnings
    documents_to_collect TEXT[], -- Array of document types
    when_to_seek_lawyer TEXT,
    risk_level VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    related_citations TEXT[], -- Array of citation strings
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scenario_guides_risk ON scenario_guides(risk_level);
CREATE INDEX idx_scenario_guides_title ON scenario_guides(scenario_title);

-- ============================================================================
-- DATASET VERSIONS
-- Tracks legal-data versions (only one active at a time)
-- ============================================================================
CREATE TABLE dataset_versions (
    id SERIAL PRIMARY KEY,
    version_name VARCHAR(255) NOT NULL UNIQUE, -- e.g., "2026-05-14-initial"
    status VARCHAR(50) NOT NULL DEFAULT 'building', -- 'building', 'ready', 'active', 'failed', 'archived'
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    activated_at TIMESTAMPTZ,
    notes TEXT,
    created_by VARCHAR(255) -- Admin user who created this version
);

CREATE INDEX idx_dataset_versions_status ON dataset_versions(status);
CREATE INDEX idx_dataset_versions_activated ON dataset_versions(activated_at);

-- Only one dataset can be active at a time (enforced by application logic)

-- ============================================================================
-- INGESTION JOBS
-- Tracks admin update jobs
-- ============================================================================
CREATE TABLE ingestion_jobs (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'queued', -- 'queued', 'running', 'success', 'failed'
    triggered_by VARCHAR(255), -- Admin user or 'system'
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    records_added INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    error_message TEXT,
    dataset_version_id INTEGER REFERENCES dataset_versions(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ingestion_jobs_status ON ingestion_jobs(status);
CREATE INDEX idx_ingestion_jobs_source ON ingestion_jobs(source_name);
CREATE INDEX idx_ingestion_jobs_created ON ingestion_jobs(created_at);

-- ============================================================================
-- PRIVACY-SAFE ANSWER LOGS
-- Privacy-first audit trail for quality, safety, and debugging.
--
-- IMPORTANT: This table intentionally does NOT store the full user question
-- text or full generated answer text. Real user questions in this app may
-- contain highly sensitive information (asylum facts, visa overstay, ICE
-- encounters, family details, criminal history, removal proceedings, etc.).
--
-- DO NOT store in this table or anywhere else by default:
--   - full question text
--   - full answer text
--   - personal immigration facts
--   - chat history
--   - uploaded user documents
--   - addresses
--   - A-numbers
--   - passport numbers
--   - criminal history
--   - asylum / credible fear / removal details
--
-- Only metadata (hashes, citations used, retrieved chunk ids, risk level,
-- refusal flag, latency, etc.) is logged so the team can audit retrieval
-- quality and safety without retaining sensitive personal content.
-- ============================================================================
CREATE TABLE privacy_safe_answer_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL DEFAULT gen_random_uuid(),
    question_hash VARCHAR(128), -- e.g., SHA-256/512 hex of normalized question; never the raw text
    answer_hash VARCHAR(128),   -- e.g., SHA-256/512 hex of generated answer; never the raw text
    retrieved_chunk_ids UUID[], -- IDs of legal_chunks used (no user content)
    citations_used JSONB DEFAULT '[]'::jsonb,
    dataset_version_id INTEGER REFERENCES dataset_versions(id),
    risk_level VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    user_language VARCHAR(10) DEFAULT 'en',
    refusal_triggered BOOLEAN DEFAULT FALSE,
    safety_flags JSONB DEFAULT '[]'::jsonb,
    model_name VARCHAR(100),
    embedding_model VARCHAR(100),
    latency_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_privacy_safe_answer_logs_created ON privacy_safe_answer_logs(created_at);
CREATE INDEX idx_privacy_safe_answer_logs_risk ON privacy_safe_answer_logs(risk_level);
CREATE INDEX idx_privacy_safe_answer_logs_dataset ON privacy_safe_answer_logs(dataset_version_id);
CREATE INDEX idx_privacy_safe_answer_logs_refusal ON privacy_safe_answer_logs(refusal_triggered);

-- ============================================================================
-- ADMIN USERS
-- Simple admin authentication for dashboard
-- ============================================================================
CREATE TABLE admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMPTZ
);

CREATE INDEX idx_admin_users_username ON admin_users(username);

-- ============================================================================
-- SEED DATA: Source Registry
-- ============================================================================
INSERT INTO source_registry (source_name, source_type, publisher, base_url, access_method, update_frequency, is_official) VALUES
('eCFR Title 8', 'regulation', 'GPO', 'https://www.ecfr.gov/current/title-8', 'bulk_xml', 'daily', TRUE),
('USCIS Policy Manual', 'policy', 'USCIS', 'https://www.uscis.gov/policy-manual', 'scraping', 'weekly', TRUE),
('U.S. Code Title 8 (INA)', 'statute', 'GPO', 'https://uscode.house.gov/browse.xhtml', 'api', 'monthly', TRUE),
('DOJ EOIR BIA Decisions', 'case_law', 'DOJ', 'https://www.justice.gov/eoir/bia-decisions', 'scraping', 'weekly', TRUE),
('Federal Register Immigration', 'regulation', 'GPO', 'https://www.federalregister.gov/documents/immigration', 'api', 'daily', TRUE),
('USCIS Forms and Instructions', 'form', 'USCIS', 'https://www.uscis.gov/forms', 'scraping', 'on_demand', TRUE);

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Get currently active dataset version
CREATE OR REPLACE FUNCTION get_active_dataset_version() RETURNS INTEGER AS $$
    SELECT id FROM dataset_versions WHERE status = 'active' ORDER BY activated_at DESC LIMIT 1;
$$ LANGUAGE SQL STABLE;

-- Get chunks for retrieval (hybrid search ready)
CREATE OR REPLACE FUNCTION search_legal_chunks(
    query_embedding vector(768),
    query_text TEXT,
    limit_count INTEGER DEFAULT 10
) RETURNS TABLE (
    id INTEGER,
    chunk_text TEXT,
    citation VARCHAR(255),
    topic VARCHAR(100),
    subtopic VARCHAR(100),
    risk_level VARCHAR(20),
    official_url TEXT,
    similarity_score FLOAT,
    rank_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH vector_search AS (
        SELECT 
            lc.id,
            lc.chunk_text,
            lc.citation,
            lc.topic,
            lc.subtopic,
            lc.risk_level,
            lc.official_url,
            1 - (lc.embedding <=> query_embedding) AS similarity_score,
            ts_rank(lc.search_vector, plainto_tsquery('english', query_text)) AS rank_score
        FROM legal_chunks lc
        WHERE lc.is_active = TRUE
        AND lc.dataset_version_id = get_active_dataset_version()
        ORDER BY similarity_score DESC
        LIMIT limit_count * 2 -- Get more for reranking
    ),
    keyword_search AS (
        SELECT 
            lc.id,
            lc.chunk_text,
            lc.citation,
            lc.topic,
            lc.subtopic,
            lc.risk_level,
            lc.official_url,
            1 - (lc.embedding <=> query_embedding) AS similarity_score,
            ts_rank(lc.search_vector, plainto_tsquery('english', query_text)) AS rank_score
        FROM legal_chunks lc
        WHERE lc.is_active = TRUE
        AND lc.dataset_version_id = get_active_dataset_version()
        AND lc.search_vector @@ plainto_tsquery('english', query_text)
        ORDER BY rank_score DESC
        LIMIT limit_count * 2
    ),
    combined AS (
        SELECT * FROM vector_search
        UNION
        SELECT * FROM keyword_search
    )
    SELECT 
        id,
        chunk_text,
        citation,
        topic,
        subtopic,
        risk_level,
        official_url,
        similarity_score,
        rank_score
    FROM combined
    ORDER BY (similarity_score * 0.6 + rank_score * 0.4) DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================
