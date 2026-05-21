-- MVP database snapshot queries
-- All SELECT only — no data is modified.
-- Run against Supabase staging or local PostgreSQL to inspect handoff state.
--
-- Usage (psql):
--   psql "$DATABASE_URL" -f review/validation/mvp-database-snapshot-queries.sql
--
-- Never paste DATABASE_URL with credentials into chat, docs, or issue trackers.

-- 1. All dataset versions
SELECT
    id,
    version_name,
    status,
    activated_at
FROM dataset_versions
ORDER BY version_name;


-- 2. Chunks per dataset (total, embedded, active, active+embedded)
SELECT
    dv.version_name,
    dv.status,
    COUNT(lc.id)                                                         AS total_chunks,
    COUNT(lc.id) FILTER (WHERE lc.embedding IS NOT NULL)                 AS embedded_chunks,
    COUNT(lc.id) FILTER (WHERE lc.is_active = TRUE)                      AS active_chunks,
    COUNT(lc.id) FILTER (WHERE lc.is_active = TRUE
                           AND lc.embedding IS NOT NULL)                 AS active_embedded_chunks
FROM dataset_versions dv
LEFT JOIN legal_chunks lc ON lc.dataset_version_id = dv.id
GROUP BY dv.id, dv.version_name, dv.status
ORDER BY dv.version_name;


-- 3. MVP active embedded count
--    Canonical prefixes + Supabase alias prefixes.
--    Target: 11,589  Minimum acceptable: 10,000
SELECT
    COUNT(*) FILTER (WHERE lc.is_active = TRUE AND lc.embedding IS NOT NULL) AS mvp_active_embedded
FROM legal_chunks lc
JOIN dataset_versions dv ON dv.id = lc.dataset_version_id
WHERE
    dv.version_name LIKE 'ecfr-title8-full%'
    OR lower(dv.version_name) LIKE 'ecfr-v%'
    OR dv.version_name LIKE 'ina-%'
    OR dv.version_name LIKE 'uscis-pm-%'
    OR dv.version_name LIKE 'uscis-official-pages%';


-- 4. eCFR sample active count (must be 0)
SELECT COUNT(*) AS sample_active_chunks
FROM legal_chunks lc
JOIN dataset_versions dv ON dv.id = lc.dataset_version_id
WHERE dv.version_name LIKE 'ecfr-title8-sample%'
  AND lc.is_active = TRUE;


-- 5. BIA active and embedded count (must be 0 for MVP)
SELECT
    COUNT(*) FILTER (WHERE lc.is_active = TRUE)         AS bia_active_chunks,
    COUNT(*) FILTER (WHERE lc.embedding IS NOT NULL)    AS bia_embedded_chunks
FROM legal_chunks lc
JOIN dataset_versions dv ON dv.id = lc.dataset_version_id
WHERE dv.version_name ILIKE 'bia%';


-- 6. Privacy log row count (must be 0 before smoke testing)
SELECT COUNT(*) AS privacy_log_count
FROM privacy_safe_answer_logs;
