"""Repository for compliance report persistence."""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.dtos import ComplianceReportDTO
from src.infra.db.models import ComplianceReportRecord


class ComplianceReportRepository:
    """Reads and writes structured compliance reports."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, report: ComplianceReportDTO) -> ComplianceReportDTO:
        payload = report.model_dump_json()
        record = await self.session.get(ComplianceReportRecord, report.session_id)
        if record is None:
            record = ComplianceReportRecord(
                session_id=report.session_id,
                customer_id=report.customer_id,
                agent_id=report.agent_id,
                report_json=payload,
                status="ready",
            )
            self.session.add(record)
        else:
            record.customer_id = report.customer_id
            record.agent_id = report.agent_id
            record.report_json = payload
            record.status = "ready"
        await self.session.commit()
        return report

    async def get(self, session_id: str) -> ComplianceReportDTO | None:
        statement = select(ComplianceReportRecord).where(ComplianceReportRecord.session_id == session_id)
        result = await self.session.execute(statement)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return ComplianceReportDTO.model_validate(json.loads(record.report_json))
