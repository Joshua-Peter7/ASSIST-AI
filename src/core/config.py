"""Environment-driven application settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="rt-suggestion-engine", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    database_url: str = Field(default="sqlite+aiosqlite:///./data/db/app.db", alias="DATABASE_URL")

    vector_db_provider: str = Field(default="weaviate", alias="VECTOR_DB_PROVIDER")
    weaviate_url: str = Field(default="http://localhost:8080", alias="WEAVIATE_URL")
    weaviate_class: str = Field(default="DocumentChunk", alias="WEAVIATE_CLASS")

    llm_provider: str = Field(default="noop", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    anthropic_base_url: str = Field(default="https://api.anthropic.com/v1", alias="ANTHROPIC_BASE_URL")
    gemini_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta",
        alias="GEMINI_BASE_URL",
    )
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1", alias="GROQ_BASE_URL")

    embedding_provider: str = Field(default="hash", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=128, alias="EMBEDDING_DIMENSION")

    cache_ttl_seconds: int = Field(default=3600, alias="CACHE_TTL_SECONDS")
    suggestion_ttl_seconds: int = Field(default=600, alias="SUGGESTION_TTL_SECONDS")
    upload_dir: str = Field(default="./data/uploads", alias="UPLOAD_DIR")
    max_chunk_size: int = Field(default=700, alias="MAX_CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, alias="CHUNK_OVERLAP")
    top_k_rag: int = Field(default=5, alias="TOP_K_RAG")
    session_prefetch_query: str = Field(
        default="product eligibility, pricing, objection handling, alternatives",
        alias="SESSION_PREFETCH_QUERY",
    )
    compliance_queue: str = Field(default="compliance", alias="COMPLIANCE_QUEUE")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
