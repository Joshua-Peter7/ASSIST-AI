"""Tests for deterministic suggestion generation."""

import pytest

from src.domain.models.dtos import RagContext, RetrievedChunk, SessionState, SignalObject
from src.domain.services.suggestion import SuggestionEngine
from src.infra.providers.llm import NoopLLMProvider


@pytest.mark.asyncio
async def test_suggestion_engine_returns_closest_alternative_when_no_exact_match() -> None:
    engine = SuggestionEngine(NoopLLMProvider())
    session = SessionState(session_id="sess-1", customer_id="cust-1", agent_id="agent-1")
    signal = SignalObject(
        session_id="sess-1",
        intent="price_search",
        entities={"price_max": 100000},
        confidence=0.8,
    )
    rag = RagContext(
        session_id="sess-1",
        query="budget bikes",
        answer="",
        chunks=[
            RetrievedChunk(
                chunk_id="1",
                document_id="doc-1",
                text="Premium touring bike",
                metadata={"product_name": "Himalayan 450", "price": 285000},
                score=0.9,
            )
        ],
    )
    suggestion = await engine.generate(session, signal, rag)
    assert suggestion.action == "suggest_alternative"
    assert "Himalayan 450" in suggestion.suggestion
