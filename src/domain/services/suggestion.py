"""Deterministic suggestion engine with optional LLM refinement."""

from __future__ import annotations

from math import inf

from src.domain.models.dtos import RagContext, SessionState, SignalObject, SuggestionResponse
from src.infra.providers.llm import LLMProvider, NoopLLMProvider


class SuggestionEngine:
    """Builds fast suggestions from cached knowledge and extracted signals."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    async def generate(
        self,
        session: SessionState,
        signal: SignalObject,
        rag_context: RagContext | None,
    ) -> SuggestionResponse:
        direct = self._build_direct(session.session_id, signal, rag_context)
        if self._should_refine(signal, rag_context) and not isinstance(self.llm_provider, NoopLLMProvider):
            refined = await self._refine_with_llm(signal, rag_context, direct)
            if refined is not None:
                refined.session_id = session.session_id
                refined.signal = signal
                return refined
        direct.signal = signal
        return direct

    def _build_direct(
        self,
        session_id: str,
        signal: SignalObject,
        rag_context: RagContext | None,
    ) -> SuggestionResponse:
        chunks = rag_context.chunks if rag_context else []
        price_max = signal.entities.get("price_max")
        exact_matches = []
        closest_alt = None
        min_gap = inf
        for chunk in chunks:
            price = chunk.metadata.get("price")
            if price is None:
                continue
            if price_max is not None and price <= price_max:
                exact_matches.append(chunk)
            elif price_max is not None:
                gap = price - price_max
                if gap >= 0 and gap < min_gap:
                    min_gap = gap
                    closest_alt = chunk
        if exact_matches:
            best = sorted(exact_matches, key=lambda item: item.metadata.get("price", 0))[0]
            product = best.metadata.get("product_name") or "matching option"
            price = int(best.metadata.get("price"))
            return SuggestionResponse(
                session_id=session_id,
                suggestion=f"Offer {product} at INR {price:,} and confirm fit against the stated budget.",
                action="recommend_match",
                priority="high" if signal.intent == "buying_signal" else "medium",
                source="rule",
            )
        if closest_alt is not None:
            product = closest_alt.metadata.get("product_name") or "closest option"
            price = int(closest_alt.metadata.get("price"))
            return SuggestionResponse(
                session_id=session_id,
                suggestion=f"No exact budget match is cached; position {product} at INR {price:,} as the closest alternative.",
                action="suggest_alternative",
                priority="medium",
                source="rule",
            )
        if rag_context and rag_context.answer:
            return SuggestionResponse(
                session_id=session_id,
                suggestion=rag_context.answer[:220],
                action="share_guidance",
                priority="medium",
                source="rule",
            )
        return SuggestionResponse(
            session_id=session_id,
            suggestion="Acknowledge the customer request and gather one more qualifying detail before recommending an option.",
            action="qualify_need",
            priority="medium",
            source="rule",
        )

    def _should_refine(self, signal: SignalObject, rag_context: RagContext | None) -> bool:
        return bool(rag_context and len(rag_context.chunks) > 2 and signal.confidence < 0.6)

    async def _refine_with_llm(
        self,
        signal: SignalObject,
        rag_context: RagContext | None,
        direct: SuggestionResponse,
    ) -> SuggestionResponse | None:
        payload = {
            "conversation": {
                "last_user_message": signal.transcript_excerpt or "",
                "intent": signal.intent,
                "filters": signal.entities,
            },
            "data": {
                "matched_products": [
                    {
                        "product_name": chunk.metadata.get("product_name"),
                        "price": chunk.metadata.get("price"),
                    }
                    for chunk in (rag_context.chunks[:3] if rag_context else [])
                    if chunk.metadata.get("product_name")
                ],
                "fallback_products": [
                    {
                        "product_name": chunk.metadata.get("product_name"),
                        "price": chunk.metadata.get("price"),
                    }
                    for chunk in (rag_context.chunks[3:5] if rag_context else [])
                    if chunk.metadata.get("product_name")
                ],
            },
            "business_rules": {"currency": "INR", "goal": "convert_customer"},
        }
        system_prompt = (
            "Return only JSON with keys suggestion, action, priority. "
            "Keep the suggestion short, actionable, and business-oriented. "
            "Use only the provided structured input and prefer closest alternatives when no match exists."
        )
        try:
            response = await self.llm_provider.generate_json(system_prompt, payload)
            return SuggestionResponse(
                session_id="",
                suggestion=response["suggestion"],
                action=response["action"],
                priority=response["priority"],
                source="llm",
            )
        except Exception:
            return None
