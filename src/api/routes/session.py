"""Session lifecycle endpoints."""

from fastapi import APIRouter, Depends

from src.bootstrap import get_session_manager
from src.core.exceptions import NotFoundError
from src.domain.models.dtos import ReportResponse, SessionEndRequest, SessionResponse, SessionStartRequest
from src.domain.services.session_manager import SessionManager
from src.infra.queue.celery_app import celery_app

router = APIRouter(tags=["sessions"])


@router.post("/session/start", response_model=SessionResponse)
async def start_session(
    request: SessionStartRequest,
    service: SessionManager = Depends(get_session_manager),
) -> SessionResponse:
    return await service.start_session(request)


@router.post("/session/end", response_model=ReportResponse)
async def end_session(
    request: SessionEndRequest,
    service: SessionManager = Depends(get_session_manager),
) -> ReportResponse:
    state = await service.end_session(request.session_id)
    if state is None:
        raise NotFoundError("Session not found")
    celery_app.send_task("generate_compliance_report", args=[request.session_id])
    return ReportResponse(session_id=request.session_id, status="pending", report=None)
