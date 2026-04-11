"""Real-time suggestion read endpoint."""

from fastapi import APIRouter, Depends, Query

from src.bootstrap import get_session_manager
from src.core.exceptions import NotFoundError
from src.domain.models.dtos import SuggestionResponse
from src.domain.services.session_manager import SessionManager

router = APIRouter(tags=["suggestions"])


@router.get("/suggestion", response_model=SuggestionResponse)
async def get_current_suggestion(
    session_id: str = Query(...),
    service: SessionManager = Depends(get_session_manager),
) -> SuggestionResponse:
    session = await service.get_session(session_id)
    if session is None or session.latest_suggestion is None:
        raise NotFoundError("No suggestion available for the session")
    return session.latest_suggestion
