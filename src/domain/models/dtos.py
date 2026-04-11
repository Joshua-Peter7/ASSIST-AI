"""Typed DTOs shared across API, services, and infrastructure."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    customer_id: str
    segment: str | None = None
    product_name: str | None = None
    price: float | None = None
    tags: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    metadata: DocumentMetadata


class SessionStartRequest(BaseModel):
    session_id: str
    customer_id: str
    agent_id: str
    metadata_filters: dict[str, Any] = Field(default_factory=dict)
    rag_seed_query: str | None = None
    call_context: str | None = None


class SessionResponse(BaseModel):
    session_id: str
    status: str
    rag_cache_key: str


class TranscriptChunkRequest(BaseModel):
    session_id: str
    speaker: Literal["agent", "customer", "system"] = "customer"
    text: str
    timestamp_ms: int | None = None
    is_final: bool = True


class TranscriptChunk(BaseModel):
    session_id: str
    speaker: str
    text: str
    timestamp_ms: int | None = None
    received_at: datetime = Field(default_factory=datetime.utcnow)
    is_final: bool = True


class SignalObject(BaseModel):
    session_id: str
    intent: str = "general"
    sentiment: str = "neutral"
    tone: str = "neutral"
    entities: dict[str, Any] = Field(default_factory=dict)
    urgency: str = "medium"
    confidence: float = 0.5
    transcript_excerpt: str | None = None


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    metadata: dict[str, Any]
    score: float


class RagContext(BaseModel):
    session_id: str
    query: str
    filters: dict[str, Any] = Field(default_factory=dict)
    answer: str
    chunks: list[RetrievedChunk] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class SuggestionResponse(BaseModel):
    suggestion: str
    action: str
    priority: Literal["low", "medium", "high"]
    source: Literal["rule", "llm"]
    session_id: str
    signal: SignalObject | None = None


class SessionState(BaseModel):
    session_id: str
    customer_id: str
    agent_id: str
    metadata_filters: dict[str, Any] = Field(default_factory=dict)
    rag_seed_query: str | None = None
    call_context: str | None = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None
    latest_signal: SignalObject | None = None
    latest_suggestion: SuggestionResponse | None = None


class SessionEndRequest(BaseModel):
    session_id: str


class ComplianceReportMetrics(BaseModel):
    behavior_score: int
    consumer_sentiment_timeline: list[dict[str, Any]]
    script_adherence: str
    call_duration_seconds: int
    interruption_count: int
    violations: list[str]
    summary: str


class ComplianceReportDTO(BaseModel):
    session_id: str
    customer_id: str
    agent_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metrics: ComplianceReportMetrics


class ReportResponse(BaseModel):
    session_id: str
    status: Literal["pending", "ready"]
    report: ComplianceReportDTO | None = None
