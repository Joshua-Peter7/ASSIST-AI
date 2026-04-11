"""Coordinates upload storage, parsing, chunking, embedding, and indexing."""

from __future__ import annotations

import json
from uuid import uuid4

from fastapi import UploadFile

from src.core.config import get_settings
from src.domain.models.dtos import DocumentMetadata, IngestResponse
from src.domain.services.chunking import TextChunker
from src.domain.services.document_parser import DocumentParser
from src.infra.providers.embeddings import EmbeddingProvider
from src.infra.providers.vector_store import VectorStore
from src.infra.storage.file_store import FileStore


class DocumentIngestionService:
    """Ingests user documents into the vector store with metadata."""

    def __init__(
        self,
        file_store: FileStore,
        parser: DocumentParser,
        chunker: TextChunker,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self.file_store = file_store
        self.parser = parser
        self.chunker = chunker
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    async def ingest(self, upload: UploadFile, metadata: DocumentMetadata) -> IngestResponse:
        settings = get_settings()
        document_id = str(uuid4())
        saved_path = await self.file_store.save(document_id, upload)
        raw_text = self.parser.parse(saved_path)
        chunks = self.chunker.split(raw_text)
        records = []
        for index, chunk in enumerate(chunks):
            chunk_id = f"{document_id}-{index}"
            vector = await self.embedding_provider.embed_text(chunk)
            records.append(
                {
                    "class": settings.weaviate_class,
                    "id": chunk_id,
                    "vector": vector,
                    "properties": {
                        "chunk_id": chunk_id,
                        "document_id": document_id,
                        "text": chunk,
                        "customer_id": metadata.customer_id,
                        "segment": metadata.segment,
                        "product_name": metadata.product_name,
                        "price": metadata.price,
                        "tags": metadata.tags,
                        "metadata_json": json.dumps(metadata.model_dump()),
                    },
                }
            )
        await self.vector_store.ensure_schema()
        await self.vector_store.upsert_chunks(records)
        return IngestResponse(
            document_id=document_id,
            filename=upload.filename or "unknown",
            chunk_count=len(chunks),
            metadata=metadata,
        )
