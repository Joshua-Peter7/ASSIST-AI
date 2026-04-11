"""Embedding provider abstraction and implementations."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

import httpx

from src.core.config import Settings, get_settings


class EmbeddingProvider(ABC):
    """Produces vectors for chunks and queries."""

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError


class HashEmbeddingProvider(EmbeddingProvider):
    """Generates deterministic local embeddings for dev and tests."""

    def __init__(self, dimension: int) -> None:
        self.dimension = dimension

    async def embed_text(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = list(digest)
        vector: list[float] = []
        for index in range(self.dimension):
            vector.append((values[index % len(values)] / 255.0) * 2 - 1)
        return vector


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Calls the OpenAI embeddings endpoint."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def embed_text(self, text: str) -> list[float]:
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
        payload = {"model": self.settings.embedding_model, "input": text}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.settings.openai_base_url}/embeddings",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]


def build_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    settings = settings or get_settings()
    if settings.embedding_provider == "openai":
        return OpenAIEmbeddingProvider(settings)
    return HashEmbeddingProvider(settings.embedding_dimension)
