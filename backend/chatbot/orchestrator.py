"""
Decides what to reply to a patient message. Transport-agnostic on purpose.

`handle_message()` takes a string and returns a Reply. It knows nothing about
Twilio, WhatsApp, HTTP, or FastAPI — which is what lets the whole decision chain
be built and tested before either external dependency exists. When the Twilio
account lands (ENG-1653) the webhook only has to read `Body` and `From`, call
this, and render the result as TwiML.

The chain, in order — the order is load-bearing:

  0. emergency   checked FIRST, on every message, before anything else can
                 interpret it. A patient halfway through the booking menu who
                 types "chest pain" must get the emergency reply, not "please
                 reply 1 or 2". Never move this.
  1. flow        if the patient is mid-conversation, their reply is an answer
                 to the current question, not a fresh intent. "1" only means
                 something in the context of what was asked.
  2. rules       predefined_responses/ — free, instant, predictable. An
                 appointment intent starts the scripted flow. ENG-1658.
  3. classifier  the outsourced ML model, routing extracted symptoms to one of
                 12 specializations. Runs ONLY when `symptoms` is supplied —
                 see below. ENG-1660.
  4. llm         OpenAI fallback for general wellness questions. ENG-1659.
  5. canned      a safe reply routing to staff when 3 and 4 are unavailable.

Layers 3 and 4 share one contract — return None for "not mine, try the next
layer" — so absent, disabled, unsure, and broken all degrade identically.


THE TWO OPTIONAL PARAMETERS
---------------------------
`phone` keys the conversation state. Without it the scripted flow is disabled
and the system behaves statelessly, which is how the tests that predate the
flow still pass, and how you can exercise the chain from a REPL.

`symptoms` comes from the scripted flow after a *separate* OpenAI extraction
call turns the patient's free-text description into symptom terms. The
classifier never reads raw WhatsApp text. That extraction step does not exist
yet, so today nothing passes `symptoms` and layer 3 stays dormant.

Reply.source records which layer answered — the measurement Phase 2's exit
criterion asks for, and every source="canned" is a keyword missing from
rules.py.
"""

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

# One engine per process. Swap `engine.store` for a Mongo-backed store in
# Phase 3; nothing else here changes.
engine = ConversationEngine()

# Rule names that open the scripted question flow instead of answering directly.
FLOW_TRIGGERS = {"appointment": "appointment"}

CANNED_REPLY = (
    "Sorry, I didn't quite understand that. A member of our staff will get "
    "back to you shortly. For anything urgent, please call the clinic directly."
)


def _classification_reply(result: Classification) -> str:
    """Turn a classification into patient-visible text.

    The safety boundary for layer 3. This routes — which department — and never
    names a condition, however confident the model is. The model is trained on
    diseases but returns only a specialization, so a disease name has no path
    to a patient. Nothing here confirms a booking either: a receptionist
    confirms every appointment.
    """
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
    # Set when the scripted flow finishes, carrying the collected answers for
    # the Appointment Engine (ENG-1664) to turn into a pending appointment.
    collected: dict[str, str] | None = None

    @property
    def used_llm(self) -> bool:
        return self.source == "llm"


def handle_message(
    message: str,
    phone: str | None = None,
    symptoms: Sequence[str] | None = None,
) -> Reply:
    """Run one patient message through the chain. Never raises."""

    # 0. Emergency pre-empts everything, including an in-progress flow. The
    #    flow is cleared rather than resumed: following an emergency reply with
    #    "so, what date suits you?" would be indefensible.
    if is_emergency(message):
        if phone:
            engine.store.clear(phone)
        return Reply(text=EMERGENCY_RESPONSE, source="emergency", matched=True)

    # 1. Mid-conversation: interpret the reply as an answer, not an intent.
    if phone:
        result = engine.advance(phone, message)
        if result is not None:
            return Reply(
                text=result.text,
                source="flow",
                matched=True,
                collected=result.data if result.finished else None,
            )

    # 2. Rules.
    rule = match_rule(message)
    if rule is not None:
        name, text = rule
        flow = FLOW_TRIGGERS.get(name)
        if flow and phone:
            logger.info("starting %s flow for %s", flow, phone)
            return Reply(
                text=engine.start(phone, flow).text, source="flow", matched=True
            )
        return Reply(text=text, source=name, matched=True)

    logger.info("unmatched message: %.120r", message)

    # 3. Classifier, only with extracted symptoms.
    if symptoms:
        result = classifier.classify(symptoms)
        if result is not None:
            logger.info(
                "classified %r -> %s (%.2f)",
                list(symptoms),
                result.specialization,
                result.confidence,
            )
            return Reply(
                text=_classification_reply(result),
                source="classifier",
                matched=False,
                classification=result,
            )

    # 4. Strip and re-check rather than trusting the caller: a whitespace-only
    #    string is truthy, and would go out as a blank WhatsApp message.
    llm_text = (llm_fallback.generate_fallback_reply(message) or "").strip()
    if llm_text:
        return Reply(text=llm_text, source="llm", matched=False)

    return Reply(text=CANNED_REPLY, source="canned", matched=False)
