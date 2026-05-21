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
from app.services.ollama_embedding_client import (
    EmbeddingClientError,
    embed_query,
    format_pgvector_literal,
)
from app.services.retrieval_scoring import (
    compute_relevance_boost,
    dedupe_by_citation,
    extract_supplemental_phrases,
    is_bia_chunk,
    query_mentions_bia,
)

# Must stay in sync with scripts/validate_hybrid_retrieval_results.py.
_RRF_K = 60

# Keyword signal is down-weighted vs vector — reduces BIA/noisy FTS dominance on
# short definitional queries ("what is a notice to appear").
_VECTOR_RRF_WEIGHT = 1.0
_KEYWORD_RRF_WEIGHT = 0.72

# Candidate pool sizes fed into RRF before final top_k truncation.
_VECTOR_CANDIDATES = 15
_KEYWORD_CANDIDATES = 15

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
    ) -> tuple[list[RetrievalResult], str | None]:
        """Run hybrid retrieval for a single query.

        Embeds the query locally with Ollama nomic-embed-text, runs
        pgvector cosine-distance search and PostgreSQL plainto_tsquery
        full-text search over ``legal_chunks WHERE is_active = TRUE``,
        fuses both ranked lists with Reciprocal Rank Fusion (RRF_K=60),
        and returns ranked RetrievalResult objects.

        Parameters
        ----------
        query:
            Query text. Whitespace is stripped; the text is never
            written to any database table.
        top_k:
            Maximum number of results to return (1–10).

        Returns
        -------
        (results, active_dataset_name)
            ``results`` — ranked list of :class:`RetrievalResult`.
            ``active_dataset_name`` — ``version_name`` of the active
            dataset, or ``None`` if none is active.

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
                active_dataset = await self._fetch_active_dataset(cur)
                vector_rows = await self._vector_search(cur, vec_literal)
                keyword_rows = await self._keyword_search(cur, stripped)
                keyword_rows = self._filter_keyword_candidates(keyword_rows, stripped)
                for phrase in extract_supplemental_phrases(stripped):
                    extra = await self._phrase_keyword_search(cur, phrase)
                    keyword_rows = self._merge_keyword_rows(keyword_rows, extra)

        fused = self._fuse_rrf(
            vector_rows,
            keyword_rows,
            top_k,
            query=stripped,
        )

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
            )
            for rank, row in enumerate(fused, start=1)
        ]

        return results, active_dataset

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _fetch_active_dataset(cur: Any) -> str | None:
        """Return the version_name of the currently active dataset, or None."""
        await cur.execute(
            "SELECT version_name FROM dataset_versions WHERE status = 'active' LIMIT 1"
        )
        row = await cur.fetchone()
        return row[0] if row else None

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
                lc.embedding <-> %s::vector             AS distance,
                LEFT(lc.chunk_text, %s)                 AS snippet
            FROM legal_chunks lc
            WHERE lc.is_active = TRUE
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
                "distance": float(r[6]) if r[6] is not None else None,
                "snippet": r[7] or "",
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
                ts_rank_cd(lc.search_vector, plainto_tsquery('english', %s)) AS kw_score,
                LEFT(lc.chunk_text, %s)                                     AS snippet
            FROM legal_chunks lc
            WHERE lc.is_active = TRUE
              AND lc.search_vector IS NOT NULL
              AND lc.search_vector @@ plainto_tsquery('english', %s)
            ORDER BY ts_rank_cd(lc.search_vector, plainto_tsquery('english', %s)) DESC
            LIMIT %s
            """,
            (query, _SNIPPET_LEN, query, query, _KEYWORD_CANDIDATES),
        )
        return RetrievalService._rows_from_keyword_fetch(await cur.fetchall())

    @staticmethod
    async def _phrase_keyword_search(
        cur: Any,
        phrase: str,
    ) -> list[dict[str, Any]]:
        """Supplemental phrase match for definitional queries (e.g. notice to appear)."""
        await cur.execute(
            """
            SELECT
                lc.id                                                       AS chunk_id,
                lc.citation,
                lc.topic,
                lc.subtopic,
                lc.risk_level,
                lc.official_url,
                ts_rank_cd(lc.search_vector, phraseto_tsquery('english', %s)) AS kw_score,
                LEFT(lc.chunk_text, %s)                                     AS snippet
            FROM legal_chunks lc
            WHERE lc.is_active = TRUE
              AND lc.search_vector IS NOT NULL
              AND lc.search_vector @@ phraseto_tsquery('english', %s)
              AND lc.citation NOT LIKE %s
              AND lc.citation NOT LIKE %s
            ORDER BY ts_rank_cd(lc.search_vector, phraseto_tsquery('english', %s)) DESC
            LIMIT %s
            """,
            (phrase, _SNIPPET_LEN, phrase, "%BIA%", "%I&N Dec.%", phrase, 12),
        )
        rows = RetrievalService._rows_from_keyword_fetch(await cur.fetchall())
        return [
            r
            for r in rows
            if not is_bia_chunk(r.get("citation", ""), r.get("topic"))
        ]

    @staticmethod
    def _rows_from_keyword_fetch(rows: list[Any]) -> list[dict[str, Any]]:
        return [
            {
                "chunk_id": r[0],
                "citation": r[1],
                "topic": r[2],
                "subtopic": r[3],
                "risk_level": r[4],
                "official_url": r[5],
                "kw_score": float(r[6]) if r[6] is not None else None,
                "snippet": r[7] or "",
            }
            for r in rows
        ]

    @staticmethod
    def _filter_keyword_candidates(
        rows: list[dict[str, Any]],
        query: str,
    ) -> list[dict[str, Any]]:
        """Drop BIA precedent chunks from keyword pool unless the query asks for them."""
        if query_mentions_bia(query):
            return rows
        return [
            r
            for r in rows
            if not is_bia_chunk(r.get("citation", ""), r.get("topic"))
        ]

    @staticmethod
    def _merge_keyword_rows(
        primary: list[dict[str, Any]],
        extra: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Merge supplemental phrase hits; keep best kw_score per chunk_id."""
        by_id: dict[int, dict[str, Any]] = {r["chunk_id"]: r for r in primary}
        for row in extra:
            cid = row["chunk_id"]
            prev = by_id.get(cid)
            if prev is None or (row.get("kw_score") or 0) > (prev.get("kw_score") or 0):
                by_id[cid] = row
        merged = list(by_id.values())
        merged.sort(key=lambda r: r.get("kw_score") or 0, reverse=True)
        return merged[:_KEYWORD_CANDIDATES]

    @staticmethod
    def _fuse_rrf(
        vector_rows: list[dict[str, Any]],
        keyword_rows: list[dict[str, Any]],
        top_k: int,
        *,
        query: str = "",
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
            rrf_v = _VECTOR_RRF_WEIGHT / (_RRF_K + rank)
            combined[cid] = {
                "chunk_id": cid,
                "citation": row["citation"],
                "topic": row["topic"],
                "subtopic": row["subtopic"],
                "risk_level": row["risk_level"],
                "official_url": row["official_url"],
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
            rrf_k = _KEYWORD_RRF_WEIGHT / (_RRF_K + rank)
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
                    "snippet": row["snippet"],
                    "vector_rank": None,
                    "vector_distance": None,
                    "keyword_rank": rank,
                    "kw_score": row["kw_score"],
                    "rrf_vector": 0.0,
                    "rrf_keyword": rrf_k,
                    "hybrid_score": rrf_k,
                }

        for row in combined.values():
            row["hybrid_score"] += compute_relevance_boost(
                query,
                citation=row["citation"],
                topic=row.get("topic"),
                subtopic=row.get("subtopic"),
                snippet=row.get("snippet") or "",
                official_url=row.get("official_url"),
            )

        ranked = sorted(combined.values(), key=lambda x: x["hybrid_score"], reverse=True)
        ranked = dedupe_by_citation(ranked)
        return ranked[:top_k]
