"""Service factory helpers shared by the API app and worker."""

from functools import lru_cache

from src.domain.services.chunking import TextChunker
from src.domain.services.compliance import ComplianceService
from src.domain.services.document_ingestion import DocumentIngestionService
from src.domain.services.document_parser import DocumentParser
from src.domain.services.rag import RagService
from src.domain.services.session_manager import SessionManager
from src.domain.services.signal_extraction import SignalExtractionService
from src.domain.services.suggestion import SuggestionEngine
from src.domain.services.transcript import TranscriptService
from src.infra.db.repository import ComplianceReportRepository
from src.infra.providers.cache import RedisCache
from src.infra.providers.embeddings import build_embedding_provider
from src.infra.providers.llm import build_llm_provider
from src.infra.providers.vector_store import build_vector_store
from src.infra.storage.file_store import FileStore


@lru_cache(maxsize=1)
def get_cache() -> RedisCache:
    return RedisCache.from_url()


@lru_cache(maxsize=1)
def get_embedding_provider():
    return build_embedding_provider()


@lru_cache(maxsize=1)
def get_vector_store():
    return build_vector_store()


@lru_cache(maxsize=1)
def get_llm_provider():
    return build_llm_provider()


@lru_cache(maxsize=1)
def get_document_ingestion_service() -> DocumentIngestionService:
    return DocumentIngestionService(
        file_store=FileStore(),
        parser=DocumentParser(),
        chunker=TextChunker(),
        embedding_provider=get_embedding_provider(),
        vector_store=get_vector_store(),
    )


@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    return RagService(
        embedding_provider=get_embedding_provider(),
        vector_store=get_vector_store(),
        llm_provider=get_llm_provider(),
        cache=get_cache(),
    )


@lru_cache(maxsize=1)
def get_session_manager() -> SessionManager:
    return SessionManager(cache=get_cache(), rag_service=get_rag_service())


@lru_cache(maxsize=1)
def get_signal_service() -> SignalExtractionService:
    return SignalExtractionService()


@lru_cache(maxsize=1)
def get_suggestion_engine() -> SuggestionEngine:
    return SuggestionEngine(llm_provider=get_llm_provider())


@lru_cache(maxsize=1)
def get_transcript_service() -> TranscriptService:
    return TranscriptService(
        cache=get_cache(),
        sessions=get_session_manager(),
        rag_service=get_rag_service(),
        signal_service=get_signal_service(),
        suggestion_engine=get_suggestion_engine(),
    )


def get_compliance_service(db_session) -> ComplianceService:
    return ComplianceService(
        transcript_service=get_transcript_service(),
        signal_service=get_signal_service(),
        llm_provider=get_llm_provider(),
        report_repository=ComplianceReportRepository(db_session),
        cache=get_cache(),
    )
