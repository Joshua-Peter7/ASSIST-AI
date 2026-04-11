"""Compliance report retrieval endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.bootstrap import get_cache
from src.api.dependencies import db_session_dependency
from src.core.exceptions import NotFoundError
from src.domain.models.dtos import ReportResponse
from src.infra.db.repository import ComplianceReportRepository
from src.infra.providers.cache import session_report_status_key

router = APIRouter(tags=["reports"])


@router.get("/report/{session_id}", response_model=ReportResponse)
async def get_report(
    session_id: str,
    db_session: AsyncSession = Depends(db_session_dependency),
) -> ReportResponse:
    repository = ComplianceReportRepository(db_session)
    report = await repository.get(session_id)
    if report is not None:
        return ReportResponse(session_id=session_id, status="ready", report=report)
    status_payload = await get_cache().get_json(session_report_status_key(session_id))
    if status_payload is not None:
        return ReportResponse(session_id=session_id, status="pending", report=None)
    raise NotFoundError("Compliance report not found")
