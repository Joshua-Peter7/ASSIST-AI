"""Handles transcript buffering and state updates for Soniox text callbacks."""

from __future__ import annotations

from src.core.exceptions import NotFoundError
from src.domain.models.dtos import TranscriptChunk
from src.domain.services.rag import RagService
from src.domain.services.session_manager import SessionManager
from src.domain.services.signal_extraction import SignalExtractionService
from src.domain.services.suggestion import SuggestionEngine
from src.infra.providers.cache import RedisCache, session_transcript_key


class TranscriptService:
    """Stores transcript chunks and refreshes derived session state."""

    def __init__(
        self,
        cache: RedisCache,
        sessions: SessionManager,
        rag_service: RagService,
        signal_service: SignalExtractionService,
        suggestion_engine: SuggestionEngine,
    ) -> None:
        self.cache = cache
        self.sessions = sessions
        self.rag_service = rag_service
        self.signal_service = signal_service
        self.suggestion_engine = suggestion_engine

    async def receive_chunk(self, request: TranscriptChunk) -> None:
        session = await self.sessions.get_session(request.session_id)
        if session is None:
            raise NotFoundError("Session not found")
        await self.cache.append_json_list(
            session_transcript_key(request.session_id),
            request.model_dump(mode="json"),
        )
        rag_context = await self.rag_service.get_cached_context(request.session_id)
        signal = self.signal_service.extract(request.session_id, request, rag_context)
        session.latest_signal = signal
        session.latest_suggestion = await self.suggestion_engine.generate(session, signal, rag_context)
        await self.sessions.save_session(session)

    async def get_transcript(self, session_id: str) -> list[TranscriptChunk]:
        payload = await self.cache.get_json(session_transcript_key(session_id)) or []
        return [TranscriptChunk.model_validate(item) for item in payload]
