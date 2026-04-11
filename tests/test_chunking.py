"""Tests for deterministic chunking behavior."""

from src.domain.services.chunking import TextChunker


def test_chunker_splits_long_text_with_overlap() -> None:
    chunker = TextChunker(max_chunk_size=20, overlap=5)
    chunks = chunker.split("alpha beta gamma delta epsilon zeta eta theta iota kappa")
    assert len(chunks) >= 3
    assert chunks[0].startswith("alpha")
    assert "epsilon" in "".join(chunks)
