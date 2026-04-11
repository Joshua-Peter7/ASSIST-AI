"""Tests for non-LLM signal extraction."""

from src.domain.models.dtos import TranscriptChunk
from src.domain.services.signal_extraction import SignalExtractionService


def test_signal_extraction_detects_budget_and_sentiment() -> None:
    service = SignalExtractionService()
    signal = service.extract(
        "sess-1",
        TranscriptChunk(
            session_id="sess-1",
            speaker="customer",
            text="Show me a bike under INR 100000, this is too expensive.",
            timestamp_ms=1000,
        ),
    )
    assert signal.intent == "price_search"
    assert signal.sentiment == "negative"
    assert signal.entities["price_max"] == 100000
