"""Deterministic text chunking for ingestion."""

from src.core.config import get_settings


class TextChunker:
    """Splits long text into overlapping chunks."""

    def __init__(self, max_chunk_size: int | None = None, overlap: int | None = None) -> None:
        settings = get_settings()
        self.max_chunk_size = max_chunk_size or settings.max_chunk_size
        self.overlap = overlap or settings.chunk_overlap

    def split(self, text: str) -> list[str]:
        cleaned = " ".join(text.split())
        if not cleaned:
            return []
        chunks: list[str] = []
        start = 0
        while start < len(cleaned):
            end = min(len(cleaned), start + self.max_chunk_size)
            if end < len(cleaned):
                split_at = cleaned.rfind(" ", start, end)
                if split_at > start:
                    end = split_at
            chunk = cleaned[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(cleaned):
                break
            start = max(0, end - self.overlap)
        return chunks
