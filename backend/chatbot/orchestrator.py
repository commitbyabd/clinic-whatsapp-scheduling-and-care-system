"""Decides what to reply to a patient message. Knows nothing about HTTP or Twilio."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Sequence

from chatbot import classifier
from chatbot import llm_fallback
from chatbot.classifier import Classification
from chatbot.conversation import ConversationEngine
from chatbot.predefined_responses.response import (
    EMERGENCY_RESPONSE,
    is_emergency,
    match_rule,
)

logger = logging.getLogger(__name__)

# one engine per process. Phase 3 swaps engine.store for a Mongo-backed one.
engine = ConversationEngine()

# rule names that open the scripted flow instead of answering directly
FLOW_TRIGGERS = {"appointment": "appointment"}

CANNED_REPLY = (
    "Sorry, I didn't quite understand that. A member of our staff will get "
    "back to you shortly. For anything urgent, please call the clinic directly."
)


def _classification_reply(result: Classification) -> str:
    # routes to a department, never names a condition. The model is trained on
    # diseases but only ever returns a specialization, so none can leak here.
    return (
        "Thanks for describing that. Based on what you've shared, our "
        f"{result.specialization} would be the right fit. Please share a "
        "preferred date and time, and our staff will confirm your appointment."
    )


@dataclass(frozen=True)
class Reply:
    text: str
    source: str
    matched: bool
    classification: Classification | None = None
    # populated when a booking flow finishes, for the Appointment Engine
    collected: dict[str, str] | None = None

    @property
    def used_llm(self) -> bool:
        return self.source == "llm"


def handle_message(
    message: str,
    phone: str | None = None,
    symptoms: Sequence[str] | None = None,
) -> Reply:
    """Run one message through the chain. Never raises.

    phone keys the conversation state; without it the scripted flow is off.
    symptoms comes from the flow after OpenAI extraction; without it the
    classifier is skipped.
    """
    # Emergency first, on every message. A patient mid-menu who types "chest
    # pain" must not have it read as a menu answer. Do not move this.
    if is_emergency(message):
        # clear the flow rather than resume it; following an emergency reply
        # with "so what date suits you?" would be indefensible
        if phone:
            engine.store.clear(phone)
        return Reply(text=EMERGENCY_RESPONSE, source="emergency", matched=True)

    if phone:
        result = engine.advance(phone, message)
        if result is not None:
            return Reply(
                text=result.text,
                source="flow",
                matched=True,
                collected=result.data if result.finished else None,
            )

    rule = match_rule(message)
    if rule is not None:
        name, text = rule
        flow = FLOW_TRIGGERS.get(name)
        if flow and phone:
            logger.info("starting %s flow", flow)
            return Reply(
                text=engine.start(phone, flow).text, source="flow", matched=True
            )
        return Reply(text=text, source=name, matched=True)

    # every one of these is a keyword missing from rules.py
    logger.info("no rule matched")

    if symptoms:
        result = classifier.classify(symptoms)
        if result is not None:
            logger.info(
                "classified as %s (%.2f)", result.specialization, result.confidence
            )
            return Reply(
                text=_classification_reply(result),
                source="classifier",
                matched=False,
                classification=result,
            )

    # strip and re-check: a whitespace-only string is truthy and would go out
    # as a blank WhatsApp message
    llm_text = (llm_fallback.generate_fallback_reply(message) or "").strip()
    if llm_text:
        return Reply(text=llm_text, source="llm", matched=False)

    return Reply(text=CANNED_REPLY, source="canned", matched=False)
