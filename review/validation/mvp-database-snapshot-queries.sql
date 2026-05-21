-- MVP database handoff validation (read-only)
-- Usage: psql "$DATABASE_URL" -f review/validation/mvp-database-snapshot-queries.sql

\echo '=== dataset_versions ==='
SELECT id, version_name, status, activated_at::date AS activated
FROM dataset_versions
ORDER BY id;

\echo '=== chunks per dataset ==='
SELECT dv.version_name, dv.status,
       COUNT(lc.id) AS total_chunks,
       COUNT(lc.embedding) AS embedded,
       COUNT(*) FILTER (WHERE lc.is_active) AS active_chunks
FROM dataset_versions dv
LEFT JOIN legal_chunks lc ON lc.dataset_version_id = dv.id
GROUP BY dv.id, dv.version_name, dv.status
ORDER BY dv.id;

\echo '=== MVP active embedded (target handoff) ==='
SELECT dv.version_name, COUNT(*) AS n
FROM legal_chunks lc
JOIN dataset_versions dv ON dv.id = lc.dataset_version_id
WHERE lc.is_active AND lc.embedding IS NOT NULL
  AND dv.version_name IN (
    'ecfr-title8-full-2026-05-11',
    'uscis-pm-2026-05-19',
    'ina-2026-05-19',
    'uscis-official-pages-2026-05-20'
  )
GROUP BY dv.version_name
ORDER BY n DESC;

\echo '=== MVP total active embedded ==='
SELECT COUNT(*) AS mvp_active_embedded
FROM legal_chunks lc
JOIN dataset_versions dv ON dv.id = lc.dataset_version_id
WHERE lc.is_active AND lc.embedding IS NOT NULL
  AND dv.version_name IN (
    'ecfr-title8-full-2026-05-11',
    'uscis-pm-2026-05-19',
    'ina-2026-05-19',
    'uscis-official-pages-2026-05-20'
  );

\echo '=== eCFR sample (must be 0 active for MVP) ==='
SELECT COUNT(*) FILTER (WHERE lc.is_active) AS sample_active_chunks
FROM legal_chunks lc
JOIN dataset_versions dv ON dv.id = lc.dataset_version_id
WHERE dv.version_name = 'ecfr-title8-sample-2026-05-11';

\echo '=== BIA (must be 0 active for MVP handoff) ==='
SELECT dv.version_name,
       COUNT(*) FILTER (WHERE lc.is_active) AS active,
       COUNT(lc.embedding) AS embedded
FROM legal_chunks lc
JOIN dataset_versions dv ON dv.id = lc.dataset_version_id
WHERE dv.version_name LIKE 'bia%'
GROUP BY dv.version_name;

\echo '=== privacy_safe_answer_logs ==='
SELECT COUNT(*) AS log_rows FROM privacy_safe_answer_logs;
