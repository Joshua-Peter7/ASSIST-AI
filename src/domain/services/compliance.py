"""Background compliance analysis and report persistence."""

from __future__ import annotations

from datetime import datetime

from src.core.exceptions import NotFoundError
from src.domain.models.dtos import (
    ComplianceReportDTO,
    ComplianceReportMetrics,
    SessionState,
    TranscriptChunk,
)
from src.domain.services.signal_extraction import SignalExtractionService
from src.domain.services.transcript import TranscriptService
from src.infra.db.repository import ComplianceReportRepository
from src.infra.providers.cache import RedisCache, session_report_status_key
from src.infra.providers.llm import LLMProvider


class ComplianceService:
    """Builds structured post-call compliance reports."""

    def __init__(
        self,
        transcript_service: TranscriptService,
        signal_service: SignalExtractionService,
        llm_provider: LLMProvider,
        report_repository: ComplianceReportRepository,
        cache: RedisCache,
    ) -> None:
        self.transcript_service = transcript_service
        self.signal_service = signal_service
        self.llm_provider = llm_provider
        self.report_repository = report_repository
        self.cache = cache

    async def build_report(self, session: SessionState) -> ComplianceReportDTO:
        transcript = await self.transcript_service.get_transcript(session.session_id)
        if not transcript:
            raise NotFoundError("Transcript not found for session")
        metrics = await self._analyze(session, transcript)
        report = ComplianceReportDTO(
            session_id=session.session_id,
            customer_id=session.customer_id,
            agent_id=session.agent_id,
            created_at=datetime.utcnow(),
            metrics=metrics,
        )
        saved = await self.report_repository.upsert(report)
        await self.cache.set_json(session_report_status_key(session.session_id), {"status": "ready"})
        return saved

    async def _analyze(self, session: SessionState, transcript: list[TranscriptChunk]) -> ComplianceReportMetrics:
        duration = self._calculate_duration_seconds(transcript, session)
        interruptions = self._count_interruptions(transcript)
        sentiment_timeline = self._build_sentiment_timeline(session.session_id, transcript)
        payload = {
            "session_id": session.session_id,
            "transcript": [item.model_dump(mode="json") for item in transcript],
            "precomputed": {
                "call_duration_seconds": duration,
                "interruption_count": interruptions,
                "consumer_sentiment_timeline": sentiment_timeline,
            },
        }
        system_prompt = (
            "You are a compliance analyst. Return JSON with keys behavior_score, "
            "script_adherence, violations, summary, consumer_sentiment_timeline. "
            "Base your answer only on the provided transcript and precomputed metrics."
        )
        response = await self.llm_provider.generate_json(system_prompt, payload)
        return ComplianceReportMetrics(
            behavior_score=int(response.get("behavior_score", 80)),
            consumer_sentiment_timeline=response.get("consumer_sentiment_timeline", sentiment_timeline),
            script_adherence=response.get("script_adherence", "unknown"),
            call_duration_seconds=duration,
            interruption_count=interruptions,
            violations=response.get("violations", []),
            summary=response.get("summary", "No summary returned."),
        )

    def _calculate_duration_seconds(self, transcript: list[TranscriptChunk], session: SessionState) -> int:
        if transcript and transcript[0].timestamp_ms is not None and transcript[-1].timestamp_ms is not None:
            return max(0, (transcript[-1].timestamp_ms - transcript[0].timestamp_ms) // 1000)
        if session.ended_at:
            return int((session.ended_at - session.started_at).total_seconds())
        return 0

    def _count_interruptions(self, transcript: list[TranscriptChunk]) -> int:
        count = 0
        for previous, current in zip(transcript, transcript[1:], strict=False):
            if previous.speaker != current.speaker and current.timestamp_ms and previous.timestamp_ms:
                if current.timestamp_ms - previous.timestamp_ms < 1500:
                    count += 1
        return count

    def _build_sentiment_timeline(self, session_id: str, transcript: list[TranscriptChunk]) -> list[dict[str, object]]:
        timeline = []
        for item in transcript:
            if item.speaker != "customer":
                continue
            signal = self.signal_service.extract(session_id, item)
            minute = (item.timestamp_ms or 0) // 60000
            timeline.append({"minute": minute, "sentiment": signal.sentiment})
        return timeline or [{"minute": 0, "sentiment": "neutral"}]
