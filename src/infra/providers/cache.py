"""Redis-backed cache and session state helpers."""

from __future__ import annotations

from typing import Any

import orjson
from redis.asyncio import Redis

from src.core.config import get_settings


class RedisCache:
    """Thin JSON cache wrapper for session and RAG state."""

    def __init__(self, client: Redis) -> None:
        self.client = client
        self.settings = get_settings()

    @classmethod
    def from_url(cls, url: str | None = None) -> "RedisCache":
        return cls(Redis.from_url(url or get_settings().redis_url, decode_responses=False))

    async def get_json(self, key: str) -> Any | None:
        value = await self.client.get(key)
        if value is None:
            return None
        return orjson.loads(value)

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self.client.set(key, orjson.dumps(value), ex=ttl or self.settings.cache_ttl_seconds)

    async def append_json_list(self, key: str, value: Any, ttl: int | None = None) -> None:
        existing = await self.get_json(key) or []
        existing.append(value)
        await self.set_json(key, existing, ttl=ttl)

    async def close(self) -> None:
        await self.client.aclose()


def session_state_key(session_id: str) -> str:
    return f"session:{session_id}:state"


def session_transcript_key(session_id: str) -> str:
    return f"session:{session_id}:transcript"


def session_rag_key(session_id: str) -> str:
    return f"session:{session_id}:rag"


def session_report_status_key(session_id: str) -> str:
    return f"session:{session_id}:report-status"
