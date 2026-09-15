"""Decides what to reply to a patient message. Knows nothing about HTTP or Twilio."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Sequence

from chatbot import classifier
from chatbot import llm_fallback
from chatbot.classifier import Classification
from chatbot.conversation import (
    OFFER_FLOW,
    REASON_STEP,
    SYMPTOM_STEP,
    ConversationEngine,
    FlowResult,
)
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

# the symptom keywords. A match is read for symptoms and a booking is offered,
# the same as symptoms described without any keyword
SYMPTOM_RULE = "feeling_unwell"

CANNED_REPLY = (
    "Sorry, I didn't quite understand that. A member of our staff will get "
    "back to you shortly. For anything urgent, please call the clinic directly."
)

UNWELL_LEAD = "We understand you're not feeling well."

DECLINED_MESSAGE = "No problem. If you'd like to book later, just message us."


def _offer_note(result: Classification) -> str:
    # suggests a department, never names a condition
    return f"This sounds like something our {result.specialization} can help with."


def _routing_note(result: Classification) -> str:
    # shown mid-booking, so it leads into the next question rather than
    # asking for a date itself
    return (
        f"Thanks. Based on what you've shared, our {result.specialization} "
        "would be the right fit."
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


def _emergency_reply(routed: Classification | None = None) -> Reply:
    return Reply(
        text=EMERGENCY_RESPONSE, source="emergency", matched=True, classification=routed
    )


def _flow_reply(
    result: FlowResult, routed: Classification | None = None, lead: str = ""
) -> Reply:
    text = result.text
    if result.step is not None:
        if routed is not None:
            text = f"{_routing_note(routed)}\n\n{text}"
        elif lead:
            text = f"{lead}\n\n{text}"
    return Reply(
        text=text,
        source="flow",
        matched=True,
        classification=routed,
        collected=result.data if result.finished else None,
    )


def _symptom_answers(message: str, routed: Classification | None) -> dict[str, str]:
    # answers both the reason question and the symptoms question, so neither
    # is asked. specialization reaches the receptionist through Reply.collected
    answers = {"reason": "symptoms", "symptom_text": message}
    if routed is not None:
        answers["specialization"] = routed.specialization
    return answers


def _offer_booking(phone: str, message: str, found: Sequence[str]) -> Reply:
    routed = classifier.classify(found)
    if routed is not None and routed.emergency:
        return _emergency_reply(routed)

    logger.info("offering a booking from symptoms")
    result = engine.start(phone, OFFER_FLOW, _symptom_answers(message, routed))
    lead = _offer_note(routed) if routed is not None else UNWELL_LEAD
    return Reply(
        text=f"{lead}\n\n{result.text}",
        source="flow",
        matched=True,
        classification=routed,
    )


def _answer_offer(phone: str, message: str) -> Reply | None:
    """Yes starts the booking with the symptoms kept, no ends it politely.

    None means the message was not an answer. The offer is dropped so the
    caller reads the message afresh, and a patient asking something else is
    never stuck on "didn't catch that".
    """
    rule = match_rule(message)
    if engine.understands(phone, message):
        result = engine.advance(phone, message)
    elif rule is not None and rule[0] == "appointment":
        # "ok I'll book an appointment" is a yes
        result = engine.advance(phone, "yes")
    else:
        engine.store.clear(phone)
        return None

    answers = dict(result.data)
    if "wants_booking" not in answers:
        return _flow_reply(result)  # a cancel word
    if answers.pop("wants_booking") != "yes":
        return Reply(text=DECLINED_MESSAGE, source="flow", matched=True)
    return _flow_reply(engine.start(phone, "appointment", answers))


def handle_message(
    message: str,
    phone: str | None = None,
    symptoms: Sequence[str] | None = None,
) -> Reply:
    """Run one message through the chain. Never raises.

    phone keys the conversation state; without it the scripted flow and the
    booking offer are off. symptoms skips extraction when the caller already
    has them.
    """
    # Emergency first, on every message. A patient mid-menu who types "chest
    # pain" must not have it read as a menu answer. Do not move this.
    if is_emergency(message):
        # clear the flow rather than resume it; following an emergency reply
        # with "so what date suits you?" would be indefensible
        if phone:
            engine.store.clear(phone)
        return _emergency_reply()

    if phone:
        routed = None
        state = engine.store.get(phone)

        if state is not None and state.flow == OFFER_FLOW:
            reply = _answer_offer(phone, message)
            if reply is not None:
                return reply
            state = None

        if state is not None and state.step == SYMPTOM_STEP:
            routed = classifier.classify(symptoms or classifier.extract_symptoms(message))
            if routed is not None and routed.emergency:
                # symptoms can add up to an emergency without the patient using
                # any emergency keyword, so the rules layer above misses these
                engine.store.clear(phone)
                return _emergency_reply(routed)
            if routed is not None:
                # reaches the receptionist through Reply.collected
                state.data["specialization"] = routed.specialization
                engine.store.save(state)

        elif (
            state is not None
            and state.step == REASON_STEP
            and not engine.understands(phone, message)
        ):
            # symptoms typed instead of a menu number: take them as the answer
            # rather than replying "didn't catch that" and asking again
            found = symptoms or classifier.extract_symptoms(message)
            if found:
                routed = classifier.classify(found)
                if routed is not None and routed.emergency:
                    engine.store.clear(phone)
                    return _emergency_reply(routed)
                result = engine.fill(phone, _symptom_answers(message, routed))
                return _flow_reply(result, routed)

        result = engine.advance(phone, message)
        if result is not None:
            return _flow_reply(result, routed)

    rule = match_rule(message)
    if rule is not None:
        name, text = rule
        if phone and name == SYMPTOM_RULE:
            found = symptoms or classifier.extract_symptoms(message)
            return _offer_booking(phone, message, found)
        flow = FLOW_TRIGGERS.get(name)
        if flow and phone:
            logger.info("starting %s flow", flow)
            return _flow_reply(engine.start(phone, flow))
        return Reply(text=text, source=name, matched=True)

    # every one of these is a keyword missing from rules.py
    logger.info("no rule matched")

    if phone:
        # symptoms without a keyword, such as "blisters on my feet"
        found = symptoms or classifier.extract_symptoms(message)
        if found:
            return _offer_booking(phone, message, found)

    if symptoms:
        result = classifier.classify(symptoms)
        if result is not None and result.emergency:
            return _emergency_reply(result)
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
