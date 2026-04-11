"""Session-prefetched RAG retrieval and answer extraction."""

from __future__ import annotations

from src.core.config import get_settings
from src.domain.models.dtos import RagContext, RetrievedChunk, SessionState
from src.infra.providers.cache import RedisCache, session_rag_key
from src.infra.providers.embeddings import EmbeddingProvider
from src.infra.providers.llm import LLMProvider
from src.infra.providers.vector_store import VectorStore


class RagService:
    """Builds filtered queries, retrieves chunks, and caches session context."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        llm_provider: LLMProvider,
        cache: RedisCache,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.llm_provider = llm_provider
        self.cache = cache
        self.settings = get_settings()

    async def warm_session_context(self, session: SessionState) -> RagContext:
        query = self._build_query(session)
        vector = await self.embedding_provider.embed_text(query)
        chunks = await self.vector_store.similarity_search(
            vector=vector,
            top_k=self.settings.top_k_rag,
            filters={"customer_id": session.customer_id, **session.metadata_filters},
        )
        answer = await self._extract_answer(query, chunks)
        context = RagContext(
            session_id=session.session_id,
            query=query,
            filters={"customer_id": session.customer_id, **session.metadata_filters},
            answer=answer,
            chunks=chunks,
        )
        await self.cache.set_json(session_rag_key(session.session_id), context.model_dump(mode="json"))
        return context

    async def get_cached_context(self, session_id: str) -> RagContext | None:
        payload = await self.cache.get_json(session_rag_key(session_id))
        if payload is None:
            return None
        return RagContext.model_validate(payload)

    def _build_query(self, session: SessionState) -> str:
        parts = [session.rag_seed_query or self.settings.session_prefetch_query]
        if session.call_context:
            parts.append(session.call_context)
        for key, value in session.metadata_filters.items():
            parts.append(f"{key}:{value}")
        return " | ".join(parts)

    async def _extract_answer(self, query: str, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "No cached knowledge was found for this customer and filter set."
        payload = {
            "query": query,
            "chunks": [{"text": chunk.text, "metadata": chunk.metadata} for chunk in chunks[:3]],
        }
        system_prompt = (
            "You are a retrieval summarizer. Return JSON with one key named answer. "
            "Produce a concise sales guidance summary from the supplied chunks only."
        )
        try:
            response = await self.llm_provider.generate_json(system_prompt, payload)
            answer = response.get("answer")
            if isinstance(answer, str) and answer.strip():
                return answer
        except Exception:
            pass
        return " ".join(chunk.text[:220] for chunk in chunks[:2])
