"""LLM provider abstraction and multi-vendor implementations."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

import httpx

from src.core.config import Settings, get_settings


class LLMProvider(ABC):
    """Unified interface for text and JSON generation."""

    @abstractmethod
    async def generate_text(self, system_prompt: str, user_payload: dict[str, Any]) -> str:
        raise NotImplementedError

    async def generate_json(self, system_prompt: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        text = await self.generate_text(system_prompt, user_payload)
        return json.loads(text)


class NoopLLMProvider(LLMProvider):
    """Returns deterministic JSON for local development."""

    async def generate_text(self, system_prompt: str, user_payload: dict[str, Any]) -> str:
        if "compliance" in system_prompt.lower():
            return json.dumps(
                {
                    "behavior_score": 82,
                    "consumer_sentiment_timeline": [{"minute": 0, "sentiment": "neutral"}],
                    "script_adherence": "partial",
                    "violations": [],
                    "summary": "Local fallback report generated without a remote LLM.",
                }
            )
        return json.dumps(
            {
                "suggestion": "Acknowledge the request and present the closest qualified option from the cached knowledge base.",
                "action": "suggest_alternative",
                "priority": "medium",
            }
        )


class OpenAICompatibleProvider(LLMProvider):
    """Supports OpenAI-style chat completion APIs such as OpenAI and Groq."""

    def __init__(self, settings: Settings, base_url: str) -> None:
        self.settings = settings
        self.base_url = base_url.rstrip("/")

    async def generate_text(self, system_prompt: str, user_payload: dict[str, Any]) -> str:
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
        payload = {
            "model": self.settings.llm_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload)},
            ],
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


class AnthropicProvider(LLMProvider):
    """Calls Anthropic's messages API and expects JSON-only text."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate_text(self, system_prompt: str, user_payload: dict[str, Any]) -> str:
        headers = {
            "x-api-key": self.settings.llm_api_key,
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": self.settings.llm_model,
            "max_tokens": 512,
            "system": system_prompt,
            "messages": [{"role": "user", "content": json.dumps(user_payload)}],
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{self.settings.anthropic_base_url}/messages",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]


class GeminiProvider(LLMProvider):
    """Calls the Gemini generateContent endpoint."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate_text(self, system_prompt: str, user_payload: dict[str, Any]) -> str:
        params = {"key": self.settings.llm_api_key}
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": json.dumps(user_payload)}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{self.settings.gemini_base_url}/models/{self.settings.llm_model}:generateContent",
                params=params,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]


def build_llm_provider(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    provider = settings.llm_provider.lower()
    if provider == "openai":
        return OpenAICompatibleProvider(settings, settings.openai_base_url)
    if provider == "groq":
        return OpenAICompatibleProvider(settings, settings.groq_base_url)
    if provider == "anthropic":
        return AnthropicProvider(settings)
    if provider == "gemini":
        return GeminiProvider(settings)
    return NoopLLMProvider()
