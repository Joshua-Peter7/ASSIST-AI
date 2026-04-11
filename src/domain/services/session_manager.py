"""Session lifecycle and cached state management."""

from __future__ import annotations

from datetime import datetime

from src.domain.models.dtos import SessionResponse, SessionStartRequest, SessionState
from src.domain.services.rag import RagService
from src.infra.providers.cache import RedisCache, session_report_status_key, session_state_key


class SessionManager:
    """Starts and ends sessions while keeping Redis state canonical."""

    def __init__(self, cache: RedisCache, rag_service: RagService) -> None:
        self.cache = cache
        self.rag_service = rag_service

    async def start_session(self, request: SessionStartRequest) -> SessionResponse:
        state = SessionState(
            session_id=request.session_id,
            customer_id=request.customer_id,
            agent_id=request.agent_id,
            metadata_filters=request.metadata_filters,
            rag_seed_query=request.rag_seed_query,
            call_context=request.call_context,
        )
        await self.cache.set_json(session_state_key(request.session_id), state.model_dump(mode="json"))
        await self.rag_service.warm_session_context(state)
        await self.cache.set_json(session_report_status_key(request.session_id), {"status": "pending"})
        return SessionResponse(
            session_id=request.session_id,
            status="started",
            rag_cache_key=f"session:{request.session_id}:rag",
        )

    async def get_session(self, session_id: str) -> SessionState | None:
        payload = await self.cache.get_json(session_state_key(session_id))
        if payload is None:
            return None
        return SessionState.model_validate(payload)

    async def save_session(self, state: SessionState) -> None:
        await self.cache.set_json(session_state_key(state.session_id), state.model_dump(mode="json"))

    async def end_session(self, session_id: str) -> SessionState | None:
        state = await self.get_session(session_id)
        if state is None:
            return None
        state.ended_at = datetime.utcnow()
        await self.save_session(state)
        return state
