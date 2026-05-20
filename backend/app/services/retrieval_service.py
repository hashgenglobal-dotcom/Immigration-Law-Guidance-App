"""
Hybrid retrieval service over active public legal_chunks.

PRIVACY / SECURITY RULES (must not be loosened without team review):
    * Query text is embedded locally via Ollama and held in memory only for
      the duration of a single request. It is never written to any table.
    * Only active public legal-source chunks are searched. No user data
      flows into these queries.
    * No answer generation, no chat LLM call, no public AI API.
    * privacy_safe_answer_logs is never read or written by this module.
    * SQL queries are all parameterized — no string interpolation of
      query text or vectors.

RRF constant:
    _RRF_K = 60 must stay in sync with scripts/validate_hybrid_retrieval_results.py.
    Do not change it without re-running hybrid retrieval validation.
"""

from __future__ import annotations

from typing import Any

from app.core.config import Settings, get_settings
from app.schemas.retrieval import RetrievalResult
from app.services.mvp_source_scope import (
    format_active_dataset_summary,
    source_family_from_version,
)
from app.services.ollama_embedding_client import (
    EmbeddingClientError,
    embed_query,
    format_pgvector_literal,
)

# Must stay in sync with scripts/validate_hybrid_retrieval_results.py.
_RRF_K = 60

# Candidate pool sizes fed into RRF before final top_k truncation.
# top_k is capped at 10 by RetrievalRequest, so 10 candidates per
# signal guarantees the full pool is available for fusion.
_VECTOR_CANDIDATES = 10
_KEYWORD_CANDIDATES = 10

_SNIPPET_LEN = 500  # characters of chunk_text returned as snippet


class RetrievalService:
    """Hybrid vector+keyword retrieval over active public legal_chunks.

    Stateless between calls. Instantiate once per application lifespan
    (e.g. via FastAPI dependency injection) and reuse across requests.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def retrieve_hybrid(
        self,
        query: str,
        top_k: int = 5,
    ) -> tuple[list[RetrievalResult], list[str], str | None]:
        """Run hybrid retrieval for a single query.

        Embeds the query locally with Ollama nomic-embed-text, runs
        pgvector cosine-distance search and PostgreSQL plainto_tsquery
        full-text search over active MVP chunks (``dataset_versions.status =
        'active'`` and ``legal_chunks.is_active = TRUE``), fuses both ranked
        lists with Reciprocal Rank Fusion (RRF_K=60), and returns ranked
        RetrievalResult objects.

        Parameters
        ----------
        query:
            Query text. Whitespace is stripped; the text is never
            written to any database table.
        top_k:
            Maximum number of results to return (1–10).

        Returns
        -------
        (results, active_datasets, active_dataset_summary)
            ``results`` — ranked list of :class:`RetrievalResult`.
            ``active_datasets`` — all ``version_name`` values with
            ``status = 'active'`` (MVP uses three co-active sources).
            ``active_dataset_summary`` — legacy single-string summary for
            API fields named ``active_dataset``.

        Raises
        ------
        EmbeddingClientError
            Ollama is unreachable or returned an unexpected response.
        app.db.connection.DatabaseConfigError
            ``DATABASE_URL`` is missing or malformed.
        Exception
            Database query errors propagate from the underlying psycopg
            connection; callers should catch and map them to HTTP 500.
        """
        from app.db.connection import connect  # deferred to avoid psycopg at import time

        stripped = query.strip()
        if not stripped:
            raise EmbeddingClientError("query must not be empty")

        # Embed locally — never contacts a public AI API.
        vector = await embed_query(
            stripped,
            ollama_base_url=self._settings.ollama_base_url,
        )
        vec_literal = format_pgvector_literal(vector)

        async with connect(self._settings) as conn:
            async with conn.cursor() as cur:
                active_datasets = await self._fetch_active_datasets(cur)
                vector_rows = await self._vector_search(cur, vec_literal)
                keyword_rows = await self._keyword_search(cur, stripped)

        fused = self._fuse_rrf(vector_rows, keyword_rows, top_k)

        results = [
            RetrievalResult(
                rank=rank,
                chunk_id=row["chunk_id"],
                citation=row["citation"],
                official_url=row["official_url"],
                topic=row["topic"],
                subtopic=row["subtopic"],
                risk_level=row["risk_level"],
                hybrid_score=row["hybrid_score"],
                vector_rank=row["vector_rank"],
                keyword_rank=row["keyword_rank"],
                vector_distance=row["vector_distance"],
                keyword_score=row["kw_score"],
                snippet=row["snippet"],
                dataset_version=row.get("dataset_version"),
                source_family=source_family_from_version(row.get("dataset_version")),
            )
            for rank, row in enumerate(fused, start=1)
        ]

        summary = format_active_dataset_summary(active_datasets)
        return results, active_datasets, summary

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _fetch_active_datasets(cur: Any) -> list[str]:
        """Return all dataset version names with status ``active`` (MVP co-active set)."""
        await cur.execute(
            """
            SELECT version_name
            FROM dataset_versions
            WHERE status = 'active'
            ORDER BY version_name
            """
        )
        return [row[0] for row in await cur.fetchall()]

    @staticmethod
    async def _vector_search(
        cur: Any,
        vec_literal: str,
    ) -> list[dict[str, Any]]:
        """pgvector cosine-distance search over active, embedded chunks.

        Query text is never passed to this method — only the pre-computed
        vector literal, which contains no personally identifiable information.
        """
        await cur.execute(
            """
            SELECT
                lc.id                                   AS chunk_id,
                lc.citation,
                lc.topic,
                lc.subtopic,
                lc.risk_level,
                lc.official_url,
                dv.version_name                         AS dataset_version,
                lc.embedding <-> %s::vector             AS distance,
                LEFT(lc.chunk_text, %s)                 AS snippet
            FROM legal_chunks lc
            INNER JOIN dataset_versions dv ON dv.id = lc.dataset_version_id
            WHERE dv.status = 'active'
              AND lc.is_active = TRUE
              AND lc.embedding IS NOT NULL
            ORDER BY lc.embedding <-> %s::vector
            LIMIT %s
            """,
            (vec_literal, _SNIPPET_LEN, vec_literal, _VECTOR_CANDIDATES),
        )
        return [
            {
                "chunk_id": r[0],
                "citation": r[1],
                "topic": r[2],
                "subtopic": r[3],
                "risk_level": r[4],
                "official_url": r[5],
                "dataset_version": r[6],
                "distance": float(r[7]) if r[7] is not None else None,
                "snippet": r[8] or "",
            }
            for r in await cur.fetchall()
        ]

    @staticmethod
    async def _keyword_search(
        cur: Any,
        query: str,
    ) -> list[dict[str, Any]]:
        """PostgreSQL plainto_tsquery full-text search over active chunks.

        ``query`` is passed only as a parameterized SQL value — it is
        never concatenated into a query string or written to any table.
        """
        await cur.execute(
            """
            SELECT
                lc.id                                                       AS chunk_id,
                lc.citation,
                lc.topic,
                lc.subtopic,
                lc.risk_level,
                lc.official_url,
                dv.version_name                                             AS dataset_version,
                ts_rank_cd(lc.search_vector, plainto_tsquery('english', %s)) AS kw_score,
                LEFT(lc.chunk_text, %s)                                     AS snippet
            FROM legal_chunks lc
            INNER JOIN dataset_versions dv ON dv.id = lc.dataset_version_id
            WHERE dv.status = 'active'
              AND lc.is_active = TRUE
              AND lc.search_vector IS NOT NULL
              AND lc.search_vector @@ plainto_tsquery('english', %s)
            ORDER BY ts_rank_cd(lc.search_vector, plainto_tsquery('english', %s)) DESC
            LIMIT %s
            """,
            (query, _SNIPPET_LEN, query, query, _KEYWORD_CANDIDATES),
        )
        return [
            {
                "chunk_id": r[0],
                "citation": r[1],
                "topic": r[2],
                "subtopic": r[3],
                "risk_level": r[4],
                "official_url": r[5],
                "dataset_version": r[6],
                "kw_score": float(r[7]) if r[7] is not None else None,
                "snippet": r[8] or "",
            }
            for r in await cur.fetchall()
        ]

    @staticmethod
    def _fuse_rrf(
        vector_rows: list[dict[str, Any]],
        keyword_rows: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Merge vector and keyword candidates with Reciprocal Rank Fusion.

        hybrid_score = 1/(RRF_K + vector_rank) + 1/(RRF_K + keyword_rank)

        Chunks present in only one list still receive that signal's
        contribution. Results are sorted by hybrid_score DESC and
        truncated to top_k.
        """
        combined: dict[int, dict[str, Any]] = {}

        for rank, row in enumerate(vector_rows, start=1):
            cid = row["chunk_id"]
            rrf_v = 1.0 / (_RRF_K + rank)
            combined[cid] = {
                "chunk_id": cid,
                "citation": row["citation"],
                "topic": row["topic"],
                "subtopic": row["subtopic"],
                "risk_level": row["risk_level"],
                "official_url": row["official_url"],
                "dataset_version": row.get("dataset_version"),
                "snippet": row["snippet"],
                "vector_rank": rank,
                "vector_distance": row["distance"],
                "keyword_rank": None,
                "kw_score": None,
                "rrf_vector": rrf_v,
                "rrf_keyword": 0.0,
                "hybrid_score": rrf_v,
            }

        for rank, row in enumerate(keyword_rows, start=1):
            cid = row["chunk_id"]
            rrf_k = 1.0 / (_RRF_K + rank)
            if cid in combined:
                combined[cid]["keyword_rank"] = rank
                combined[cid]["kw_score"] = row["kw_score"]
                combined[cid]["rrf_keyword"] = rrf_k
                combined[cid]["hybrid_score"] += rrf_k
            else:
                combined[cid] = {
                    "chunk_id": cid,
                    "citation": row["citation"],
                    "topic": row["topic"],
                    "subtopic": row["subtopic"],
                    "risk_level": row["risk_level"],
                    "official_url": row["official_url"],
                    "dataset_version": row.get("dataset_version"),
                    "snippet": row["snippet"],
                    "vector_rank": None,
                    "vector_distance": None,
                    "keyword_rank": rank,
                    "kw_score": row["kw_score"],
                    "rrf_vector": 0.0,
                    "rrf_keyword": rrf_k,
                    "hybrid_score": rrf_k,
                }

        ranked = sorted(
            combined.values(), key=lambda x: x["hybrid_score"], reverse=True
        )
        return ranked[:top_k]
