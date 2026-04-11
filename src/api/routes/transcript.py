"""Transcript intake endpoint for Soniox callbacks or polling pushes."""

from fastapi import APIRouter, Depends

from src.bootstrap import get_transcript_service
from src.domain.models.dtos import TranscriptChunk, TranscriptChunkRequest
from src.domain.services.transcript import TranscriptService

router = APIRouter(tags=["transcripts"])


@router.post("/transcript", status_code=202)
async def receive_transcript_chunk(
    request: TranscriptChunkRequest,
    service: TranscriptService = Depends(get_transcript_service),
) -> dict[str, str]:
    chunk = TranscriptChunk(
        session_id=request.session_id,
        speaker=request.speaker,
        text=request.text,
        timestamp_ms=request.timestamp_ms,
        is_final=request.is_final,
    )
    await service.receive_chunk(chunk)
    return {"status": "accepted"}
