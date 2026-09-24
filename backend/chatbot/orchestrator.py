"""Decides what to reply to a patient message. Knows nothing about HTTP or Twilio."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Sequence

from chatbot import classifier
from chatbot import directory
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
    RULES,
    is_emergency,
    match_rule,
)

logger = logging.getLogger(__name__)

# One engine per process. At startup main.py swaps engine.store for the
# Mongo-backed one, so the chatbot itself never learns about Mongo.
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


# Rules that answer a question about the clinic. Asked in the middle of a
# booking chat, they are answered and the chat waits where it was, rather
# than the question being taken as the answer.
INFO_RULES = frozenset(
    {"fees", "doctor_info", "clinic_hours", "location", "insurance", "contact", "services"}
)

# English and Roman Urdu openers that make a message a question even
# without a question mark
_QUESTION_START = re.compile(
    r"^\s*(what|when|where|which|who|how|is|are|do|does|did|can|could|will|"
    r"would|should|kya|kab|kahan|kaun|kitna|kitni|kitne)\b",
    re.IGNORECASE,
)


def _is_question(message: str) -> bool:
    return "?" in message or bool(_QUESTION_START.match(message))


_SCHEDULE_WORDS = re.compile(
    r"\b(schedule|schedules|timing|timings|hours|days|available|availability|"
    r"slot|slots|sit|sits|come|comes)\b",
    re.IGNORECASE,
)
_DOCTOR_WORDS = re.compile(
    r"\b(doctor|doctors|dr|physician|specialist|consultant)\b", re.IGNORECASE
)
# "can I schedule an appointment with the dermatologist?" is a booking
_BOOKING_WORDS = re.compile(r"\b(book|booking|appointment|appointments)\b", re.IGNORECASE)


def _asks_doctor_schedule(message: str) -> bool:
    """ "What is the schedule of your general physician?" The appointment
    rule would take it for a booking because it says "schedule", so it is
    recognised here first: a question naming a doctor or department and
    asking when."""
    return (
        _is_question(message)
        and bool(_SCHEDULE_WORDS.search(message))
        and bool(directory.department_in(message) or _DOCTOR_WORDS.search(message))
        and not _BOOKING_WORDS.search(message)
    )


def _named_department(message: str) -> dict[str, str]:
    # "book me with the dermatologist": the doctor menu starts there
    department = directory.department_in(message)
    return {"specialization": department} if department else {}


def _doctors_reply(message: str, in_chat: bool) -> str | None:
    """The doctors, how each sees patients, and their hours; only the ones
    in a department the message names, when it names one. None when the
    directory is missing or failed, so the fixed rule text is used."""
    department = directory.department_in(message)
    doctors = directory.find_doctors(department)
    if doctors is None:
        return None

    lead = ""
    if department and not doctors:
        lead = f"We don't have a {department} at the moment. "
        doctors = directory.find_doctors() or []
    if not doctors:
        return None

    lines = [
        f"\u2022 {doctor.name}, {doctor.specialization}: "
        f"{'first come, first served' if doctor.walk_in else 'by appointment'}, "
        f"{directory.describe_hours(doctor.hours)}"
        for doctor in doctors
    ]
    reply = f"{lead}Our doctors:\n" + "\n".join(lines)
    if not in_chat:
        reply += '\n\nTo book, reply "book an appointment".'
    return reply


# said instead when there is no directory to read the doctors from
DOCTOR_INFO_REPLY = RULES["doctor_info"]["response"]


def _schedule_reply(message: str, in_chat: bool) -> Reply:
    return Reply(
        text=_doctors_reply(message, in_chat) or DOCTOR_INFO_REPLY,
        source="doctor_info",
        matched=True,
    )


def _rule_text(name: str, text: str, message: str, in_chat: bool = False) -> str:
    if name == "doctor_info":
        return _doctors_reply(message, in_chat) or text
    return text


def _answer_aside(message: str) -> Reply | None:
    """A question about the clinic asked in the middle of a chat, answered
    without moving the chat on, or None when the message is not one."""
    if not _is_question(message):
        return None
    if _asks_doctor_schedule(message):
        return _schedule_reply(message, in_chat=True)
    rule = match_rule(message)
    if rule is None or rule[0] not in INFO_RULES:
        return None
    name, text = rule
    return Reply(text=_rule_text(name, text, message, in_chat=True), source=name, matched=True)


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
        # a cancelled or handed-off flow finishes with no data, and must not
        # look like a booking to save
        collected=result.data if result.finished and result.data else None,
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

        # "what are the doctor's timings?" at "what time suits you?" is a
        # question to answer, not the time to save
        if state is not None:
            aside = _answer_aside(message)
            if aside is not None:
                prompt = engine.current_prompt(phone)
                return Reply(
                    text=f"{aside.text}\n\n{prompt}" if prompt else aside.text,
                    source=aside.source,
                    matched=True,
                )

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

    # answered with the doctors' own hours, rather than taken for a booking
    # because the question says "schedule"
    if _asks_doctor_schedule(message):
        return _schedule_reply(message, in_chat=False)

    rule = match_rule(message)
    if rule is not None:
        name, text = rule
        if phone and name == SYMPTOM_RULE:
            found = symptoms or classifier.extract_symptoms(message)
            return _offer_booking(phone, message, found)
        flow = FLOW_TRIGGERS.get(name)
        if flow and phone:
            logger.info("starting %s flow", flow)
            return _flow_reply(engine.start(phone, flow, _named_department(message)))
        return Reply(text=_rule_text(name, text, message), source=name, matched=True)

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
