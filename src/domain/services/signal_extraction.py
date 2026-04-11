"""Rule-based signal extraction without any LLM dependency."""

from __future__ import annotations

import re

from src.domain.models.dtos import RagContext, SignalObject, TranscriptChunk


class SignalExtractionService:
    """Classifies intent, tone, sentiment, and entities from transcript text."""

    POSITIVE_WORDS = {"good", "great", "love", "interested", "yes", "works"}
    NEGATIVE_WORDS = {"bad", "expensive", "angry", "frustrated", "no", "issue", "problem"}

    def extract(self, session_id: str, chunk: TranscriptChunk, rag_context: RagContext | None = None) -> SignalObject:
        text = chunk.text.lower()
        intent = self._detect_intent(text)
        sentiment = self._detect_sentiment(text)
        tone = self._detect_tone(text)
        entities = self._extract_entities(text, rag_context)
        confidence = 0.65 if entities or intent != "general" else 0.45
        urgency = "high" if tone == "frustrated" or intent in {"buying_signal", "cancellation_risk"} else "medium"
        return SignalObject(
            session_id=session_id,
            intent=intent,
            sentiment=sentiment,
            tone=tone,
            entities=entities,
            urgency=urgency,
            confidence=confidence,
            transcript_excerpt=chunk.text[:240],
        )

    def _detect_intent(self, text: str) -> str:
        if any(token in text for token in ("buy", "purchase", "book", "sign up", "take it")):
            return "buying_signal"
        if any(token in text for token in ("under", "budget", "within", "less than")):
            return "price_search"
        if any(token in text for token in ("cancel", "leave", "not interested", "don't want")):
            return "cancellation_risk"
        if any(token in text for token in ("compare", "alternative", "other option", "another one")):
            return "alternative_request"
        return "general"

    def _detect_sentiment(self, text: str) -> str:
        score = 0
        score += sum(1 for word in self.POSITIVE_WORDS if word in text)
        score -= sum(1 for word in self.NEGATIVE_WORDS if word in text)
        if score > 0:
            return "positive"
        if score < 0:
            return "negative"
        return "neutral"

    def _detect_tone(self, text: str) -> str:
        if "!" in text or any(term in text for term in ("angry", "frustrated", "upset", "asap")):
            return "frustrated"
        if any(term in text for term in ("please", "could you", "can you")):
            return "polite"
        return "neutral"

    def _extract_entities(self, text: str, rag_context: RagContext | None) -> dict[str, object]:
        entities: dict[str, object] = {}
        price_match = re.search(r"(under|below|within|less than)\s*(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d+)?)", text)
        if price_match:
            entities["price_max"] = float(price_match.group(2).replace(",", ""))
        exact_price_match = re.search(r"(?:rs\.?|inr|₹)\s*([\d,]+(?:\.\d+)?)", text)
        if exact_price_match and "price_max" not in entities:
            entities["mentioned_price"] = float(exact_price_match.group(1).replace(",", ""))
        if any(term in text for term in ("under", "within", "below")):
            entities["constraint_type"] = "budget_cap"
        if rag_context:
            catalog = {
                str(chunk.metadata.get("product_name")).lower(): chunk.metadata.get("product_name")
                for chunk in rag_context.chunks
                if chunk.metadata.get("product_name")
            }
            for token, original in catalog.items():
                if token and token in text:
                    entities["product_name"] = original
                    break
        return entities
