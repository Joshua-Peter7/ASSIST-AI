"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.error_handlers import register_error_handlers
from src.api.routes.ingest import router as ingest_router
from src.api.routes.report import router as report_router
from src.api.routes.session import router as session_router
from src.api.routes.suggestion import router as suggestion_router
from src.api.routes.transcript import router as transcript_router
from src.bootstrap import get_cache, get_vector_store
from src.core.config import get_settings
from src.core.logging import configure_logging
from src.infra.db.database import engine
from src.infra.db.models import Base


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await get_vector_store().ensure_schema()
    yield
    await get_cache().close()


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
register_error_handlers(app)
app.include_router(ingest_router)
app.include_router(session_router)
app.include_router(transcript_router)
app.include_router(suggestion_router)
app.include_router(report_router)
