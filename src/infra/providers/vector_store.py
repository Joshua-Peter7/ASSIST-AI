"""Vector store abstraction and Weaviate implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx

from src.core.config import Settings, get_settings
from src.domain.models.dtos import RetrievedChunk


class VectorStore(ABC):
    """Stores and queries embedded document chunks."""

    @abstractmethod
    async def ensure_schema(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def upsert_chunks(self, records: list[dict[str, Any]]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def similarity_search(
        self,
        vector: list[float],
        top_k: int,
        filters: dict[str, Any],
    ) -> list[RetrievedChunk]:
        raise NotImplementedError


class WeaviateVectorStore(VectorStore):
    """HTTP-based Weaviate integration with metadata filtering."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.weaviate_url.rstrip("/")
        self.class_name = settings.weaviate_class

    async def ensure_schema(self) -> None:
        async with httpx.AsyncClient(timeout=20.0) as client:
            schema_response = await client.get(f"{self.base_url}/v1/schema")
            schema_response.raise_for_status()
            classes = schema_response.json().get("classes", [])
            if any(item["class"] == self.class_name for item in classes):
                return
            payload = {
                "class": self.class_name,
                "vectorizer": "none",
                "properties": [
                    {"name": "chunk_id", "dataType": ["text"]},
                    {"name": "document_id", "dataType": ["text"]},
                    {"name": "text", "dataType": ["text"]},
                    {"name": "customer_id", "dataType": ["text"]},
                    {"name": "segment", "dataType": ["text"]},
                    {"name": "product_name", "dataType": ["text"]},
                    {"name": "price", "dataType": ["number"]},
                    {"name": "tags", "dataType": ["text[]"]},
                    {"name": "metadata_json", "dataType": ["text"]},
                ],
            }
            create_response = await client.post(f"{self.base_url}/v1/schema", json=payload)
            create_response.raise_for_status()

    async def upsert_chunks(self, records: list[dict[str, Any]]) -> None:
        async with httpx.AsyncClient(timeout=20.0) as client:
            for record in records:
                response = await client.post(f"{self.base_url}/v1/objects", json=record)
                response.raise_for_status()

    async def similarity_search(
        self,
        vector: list[float],
        top_k: int,
        filters: dict[str, Any],
    ) -> list[RetrievedChunk]:
        where_filter = _build_weaviate_where(filters)
        args = [f"limit: {top_k}", f"nearVector: {{vector: {_format_vector(vector)}}}"]
        if where_filter:
            args.append(f"where: {where_filter}")
        query = (
            "{ Get { "
            f'{self.class_name}({", ".join(args)}) '
            "{ chunk_id document_id text customer_id segment product_name price tags metadata_json "
            "_additional { id distance } } } }"
        )
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{self.base_url}/v1/graphql", json={"query": query})
            response.raise_for_status()
            items = response.json()["data"]["Get"].get(self.class_name, [])
        results: list[RetrievedChunk] = []
        for item in items:
            results.append(
                RetrievedChunk(
                    chunk_id=item["chunk_id"],
                    document_id=item["document_id"],
                    text=item["text"],
                    metadata={
                        "customer_id": item.get("customer_id"),
                        "segment": item.get("segment"),
                        "product_name": item.get("product_name"),
                        "price": item.get("price"),
                        "tags": item.get("tags") or [],
                        "metadata_json": item.get("metadata_json"),
                    },
                    score=1 - float(item["_additional"].get("distance", 1)),
                )
            )
        return results


def _format_vector(vector: list[float]) -> str:
    return "[" + ", ".join(f"{value:.6f}" for value in vector) + "]"


def _build_weaviate_where(filters: dict[str, Any]) -> str | None:
    if not filters:
        return None
    operands: list[str] = []
    for key, value in filters.items():
        if value is None:
            continue
        if isinstance(value, (int, float)):
            operands.append(f'{{path:["{key}"], operator:LessThanEqual, valueNumber:{value}}}')
        else:
            safe = str(value).replace('"', '\\"')
            operands.append(f'{{path:["{key}"], operator:Equal, valueText:"{safe}"}}')
    if not operands:
        return None
    if len(operands) == 1:
        return operands[0]
    return "{operator:And, operands:[" + ", ".join(operands) + "]}"


def build_vector_store(settings: Settings | None = None) -> VectorStore:
    settings = settings or get_settings()
    return WeaviateVectorStore(settings)
