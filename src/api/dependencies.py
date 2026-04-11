"""FastAPI dependency helpers."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.bootstrap import (
    get_document_ingestion_service,
    get_rag_service,
    get_session_manager,
    get_signal_service,
    get_suggestion_engine,
    get_transcript_service,
)
from src.infra.db.database import get_db_session


async def db_session_dependency() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


__all__ = [
    "db_session_dependency",
    "get_document_ingestion_service",
    "get_rag_service",
    "get_session_manager",
    "get_signal_service",
    "get_suggestion_engine",
    "get_transcript_service",
]
