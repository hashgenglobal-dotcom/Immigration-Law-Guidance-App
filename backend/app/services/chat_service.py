"""
Chat service for the POST /api/chat endpoint.

PRIVACY / SECURITY RULES (must not be loosened without team review):
    * The raw user message is passed to the local Ollama chat model only.
      It is never logged, printed, persisted, or included in error messages.
    * query_hash (SHA-256 of normalized message) is the only message
      derivative that appears in ChatResponse.
    * No chat history is stored. This service is stateless between calls.
    * privacy_safe_answer_logs is never read or written by this module.
    * No public AI API is called at any point in this service.
    * Retrieval and answer generation both run against local services only.
"""

from __future__ import annotations

import hashlib

from app.core.config import Settings, get_settings
from app.schemas.chat import ChatCitation, ChatResponse, ChatUsedChunk
from app.schemas.retrieval import RetrievalResult
from app.schemas.chat import ClarificationOption
from app.services.guided_intake import (
    build_clarification,
    detect_broad_topic,
    is_valid_category_value,
    resolve_retrieval_query,
)
from app.services.ollama_chat_client import OllamaChatClient
from app.services.mvp_source_scope import mvp_source_families_from_versions
from app.services.retrieval_service import RetrievalService

_DISCLAIMER = (
    "This is general legal information only. It is not legal advice, does not create "
    "an attorney-client relationship, and does not replace a qualified immigration attorney. "
    "For urgent, high-risk, or case-specific situations, consult a qualified immigration attorney."
)

_SYSTEM_PROMPT = (
    "You are a legal information assistant, not a lawyer.\n\n"
    "Use only the retrieved legal sources provided in the user message to answer the question. "
    "Do not use any knowledge beyond these sources.\n\n"
    "Do not invent laws, deadlines, eligibility rules, form numbers, processing times, or citations. "
    "If a detail is not in the provided sources, do not state it.\n\n"
    "Answering from sources:\n"
    "- If at least one retrieved source directly answers the user's question, provide a direct answer "
    "based on that source and cite it using the exact citation string.\n"
    "- Prioritize the most directly relevant retrieved sources. Consider all provided sources, but do "
    "not force less relevant sources into the answer unless they genuinely help.\n"
    "- Do not include a generic uncertainty statement after giving a direct, source-supported answer.\n"
    "- Use uncertainty only for parts of the question that are not answered by the retrieved sources.\n\n"
    "If none of the retrieved sources answer the question, say clearly that you cannot answer "
    "confidently from the available sources and recommend consulting a qualified immigration attorney.\n\n"
    "When describing what a source says someone 'may request' or 'is eligible to request', explain it "
    "as eligibility to make a request — not as a guarantee of approval.\n\n"
    "Explain in plain language that a non-expert can understand.\n\n"
    "Always cite the provided source citations when making statements. "
    "Use the exact citation strings from the retrieved sources.\n\n"
    "This is general legal information, not legal advice, and does not create an "
    "attorney-client relationship.\n\n"
    "Do not provide guidance on how to commit fraud, misrepresent facts on applications, "
    "evade immigration law, avoid court appearances, or circumvent legal responsibilities. "
    "Decline such requests clearly."
)

_NO_RESULTS_ANSWER = (
    "Based on the currently available legal sources, I cannot answer confidently from the available sources. "
    "Please consult a qualified immigration attorney for guidance specific to your situation."
)


class ChatService:
    """Business logic layer for the POST /api/chat endpoint.

    Orchestrates hybrid retrieval and local Ollama answer generation.
    Stateless between calls — no chat history, no persistence.

    Parameters
    ----------
    settings:
        Application settings. Defaults to ``get_settings()``.
    retrieval_service:
        Injectable retrieval dependency. Defaults to
        ``RetrievalService(settings)``. Pass a fake in tests to avoid
        database and Ollama embedding calls.
    chat_client:
        Injectable chat dependency. Defaults to ``OllamaChatClient()``.
        Pass a fake in tests to avoid live Ollama chat calls.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        retrieval_service: object | None = None,
        chat_client: object | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._retrieval_service = retrieval_service or RetrievalService(self._settings)
        self._chat_client = chat_client or OllamaChatClient()

    async def generate_chat_response(
        self,
        message: str,
        top_k: int = 5,
        selected_category: str | None = None,
    ) -> ChatResponse:
        """Generate a grounded plain-language legal information response.

        Parameters
        ----------
        message:
            User question. Processed in memory only; never persisted or
            included in error messages.
        top_k:
            Number of hybrid-ranked chunks to retrieve and use for
            answer generation (1–10).

        Returns
        -------
        ChatResponse
            Grounded answer with citations, disclaimer, and chunk provenance.
            The raw message is never included in the response.

        Raises
        ------
        EmbeddingClientError
            Ollama embedding service is unreachable during retrieval.
        OllamaChatClientError
            Local Ollama chat model is unreachable or returned an invalid
            response. Propagates to the route layer for HTTP mapping.
        Exception
            Database errors from retrieval propagate to the route layer.
        """
        normalized = message.strip().lower()
        query_hash = hashlib.sha256(normalized.encode()).hexdigest()

        if selected_category and not is_valid_category_value(selected_category):
            selected_category = None

        if not selected_category:
            topic = detect_broad_topic(message)
            if topic:
                payload = build_clarification(topic)
                if payload:
                    return ChatResponse(
                        status="needs_clarification",
                        query_hash=query_hash,
                        answer=payload.answer,
                        clarifying_question=payload.clarifying_question,
                        options=[
                            ClarificationOption(label=o.label, value=o.value)
                            for o in payload.options
                        ],
                        citations=[],
                        disclaimer=_DISCLAIMER,
                        active_dataset=None,
                        active_datasets=[],
                        mvp_sources=[],
                        used_chunks=[],
                    )

        retrieval_query = resolve_retrieval_query(message, selected_category)

        results, active_datasets, active_dataset = (
            await self._retrieval_service.retrieve_hybrid(
                query=retrieval_query,
                top_k=top_k,
            )
        )
        mvp_sources = mvp_source_families_from_versions(active_datasets)

        if not results:
            return ChatResponse(
                query_hash=query_hash,
                answer=_NO_RESULTS_ANSWER,
                citations=[],
                disclaimer=_DISCLAIMER,
                active_dataset=active_dataset,
                active_datasets=active_datasets,
                mvp_sources=mvp_sources,
                used_chunks=[],
            )

        messages = self._build_messages(message, results, selected_category)

        answer = await self._chat_client.generate_chat_response(
            messages=messages,
            model=self._settings.ollama_chat_model,
            ollama_base_url=self._settings.ollama_chat_base_url or self._settings.ollama_base_url,
            ollama_api_key=self._settings.ollama_api_key,
        )

        return ChatResponse(
            query_hash=query_hash,
            answer=answer,
            citations=self._to_citations(results),
            disclaimer=_DISCLAIMER,
            active_dataset=active_dataset,
            active_datasets=active_datasets,
            mvp_sources=mvp_sources,
            used_chunks=self._to_used_chunks(results),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_messages(
        message: str,
        results: list[RetrievalResult],
        selected_category: str | None = None,
    ) -> list[dict[str, str]]:
        """Build the Ollama messages list from the user message and retrieved chunks.

        The raw message appears only in the user role content, which is
        passed to the local chat model and never persisted or logged.
        """
        context = ChatService._build_source_context(results)
        category_note = ""
        if selected_category:
            category_note = (
                f"\nThe user selected immigration category: {selected_category}. "
                "Focus your answer on that category only. Do not discuss unrelated pathways "
                "unless the sources require a brief cross-reference.\n"
            )
        user_content = (
            f"Question: {message}\n"
            f"{category_note}\n"
            f"Retrieved legal sources:\n{context}\n\n"
            "Answer only from the retrieved sources above. "
            "Include citations from the sources in your answer."
        )
        return [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    @staticmethod
    def _build_source_context(results: list[RetrievalResult]) -> str:
        """Format retrieved chunks into a numbered source context string.

        Produces a structured block the chat model can read and cite from.
        Includes rank, chunk_id, citation, hybrid_score, topic, subtopic,
        risk_level, official_url, and snippet for every result. Only the
        snippet (up to 500 characters) is included — not the full chunk text.
        """
        sections: list[str] = []
        for r in results:
            lines: list[str] = [f"[{r.rank}] {r.citation}"]
            lines.append(f"Chunk ID: {r.chunk_id} | Hybrid Score: {r.hybrid_score:.6f}")

            topic_parts: list[str] = []
            if r.topic:
                topic_parts.append(r.topic)
            if r.subtopic:
                topic_parts.append(r.subtopic)
            if topic_parts:
                topic_line = "Topic: " + " — ".join(topic_parts)
                if r.risk_level:
                    topic_line += f" | Risk: {r.risk_level}"
                lines.append(topic_line)

            if r.official_url:
                lines.append(r.official_url)

            if r.snippet:
                lines.append("")
                lines.append(r.snippet)

            sections.append("\n".join(lines))

        return "\n\n---\n\n".join(sections)

    @staticmethod
    def _to_citations(results: list[RetrievalResult]) -> list[ChatCitation]:
        """Build a deduplicated citation list from retrieval results.

        Deduplication is by citation string. The first occurrence (lowest
        rank) wins. Insertion order is preserved.
        """
        seen: dict[str, ChatCitation] = {}
        for r in results:
            if r.citation not in seen:
                seen[r.citation] = ChatCitation(
                    citation=r.citation,
                    official_url=r.official_url,
                    topic=r.topic,
                    subtopic=r.subtopic,
                    risk_level=r.risk_level,
                )
        return list(seen.values())

    @staticmethod
    def _to_used_chunks(results: list[RetrievalResult]) -> list[ChatUsedChunk]:
        """Map RetrievalResult objects to ChatUsedChunk response models.

        Includes rank, provenance, and snippet. Excludes retrieval-internal
        fields (vector_rank, keyword_rank, vector_distance, keyword_score)
        that are not part of the chat response contract.
        """
        return [
            ChatUsedChunk(
                rank=r.rank,
                chunk_id=r.chunk_id,
                citation=r.citation,
                official_url=r.official_url,
                topic=r.topic,
                subtopic=r.subtopic,
                risk_level=r.risk_level,
                hybrid_score=r.hybrid_score,
                snippet=r.snippet,
                dataset_version=r.dataset_version,
                source_family=r.source_family,
            )
            for r in results
        ]
