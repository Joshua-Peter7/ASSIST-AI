"""Celery worker that builds post-call compliance reports."""

import asyncio

from src.bootstrap import get_compliance_service, get_session_manager
from src.infra.db.database import AsyncSessionLocal
from src.infra.queue.celery_app import celery_app


@celery_app.task(name="generate_compliance_report")
def generate_compliance_report(session_id: str) -> dict[str, str]:
    return asyncio.run(_generate(session_id))


async def _generate(session_id: str) -> dict[str, str]:
    session_manager = get_session_manager()
    session = await session_manager.get_session(session_id)
    if session is None:
        return {"status": "missing_session"}
    async with AsyncSessionLocal() as db_session:
        compliance_service = get_compliance_service(db_session)
        await compliance_service.build_report(session)
    return {"status": "ready"}
