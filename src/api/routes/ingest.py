"""Document ingestion endpoint."""

import json

from fastapi import APIRouter, Depends, File, Form, UploadFile

from src.bootstrap import get_document_ingestion_service
from src.domain.models.dtos import DocumentMetadata, IngestResponse
from src.domain.services.document_ingestion import DocumentIngestionService

router = APIRouter(tags=["ingestion"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    customer_id: str = Form(...),
    segment: str | None = Form(default=None),
    product_name: str | None = Form(default=None),
    price: float | None = Form(default=None),
    tags: str = Form(default="[]"),
    extra: str = Form(default="{}"),
    service: DocumentIngestionService = Depends(get_document_ingestion_service),
) -> IngestResponse:
    metadata = DocumentMetadata(
        customer_id=customer_id,
        segment=segment,
        product_name=product_name,
        price=price,
        tags=json.loads(tags),
        extra=json.loads(extra),
    )
    return await service.ingest(file, metadata)
