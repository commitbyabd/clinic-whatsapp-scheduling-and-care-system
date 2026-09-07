"""Scripted question flow: numbered menus and the per-patient state behind them.

A reply like "1" only means something if you remember what was asked, so each
phone number gets a state machine tracking which step it is on.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol

logger = logging.getLogger(__name__)

# after this many unrecognised replies, hand off rather than loop forever
MAX_REPROMPTS = 2

STATE_TTL = timedelta(hours=24)

CANCEL_WORDS = frozenset(
    {"cancel", "stop", "exit", "quit", "menu", "start over", "restart", "back"}
)

_PUNCTUATION = re.compile(r"[^\w\s]+")


def _normalize(text: str) -> str:
    return _PUNCTUATION.sub(" ", text.lower()).strip()


@dataclass(frozen=True)
class Option:
    # key is what the code branches on, label is what the patient reads, so a
    # menu can be reworded without breaking the branching
    key: str
    label: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Step:
    id: str
    question: str
    options: tuple[Option, ...] = ()  # empty means a free-text answer
    field: str = ""  # where the answer goes in state.data
    next: str | Callable[[str], str | None] | None = None

    def render(self) -> str:
        if not self.options:
            return self.question
        lines = [f"{i}. {opt.label}" for i, opt in enumerate(self.options, 1)]
        return self.question + "\n\n" + "\n".join(lines)

    def match(self, reply: str) -> str | None:
        # built from the same options render() uses, so the menu and the parser
        # cannot drift apart
        text = _normalize(reply)
        if not text:
            return None

        if not self.options:
            return reply.strip()

        if text.isdigit():
            index = int(text) - 1
            if 0 <= index < len(self.options):
                return self.options[index].key
            return None

        for opt in self.options:
            candidates = {_normalize(opt.key), _normalize(opt.label)}
            candidates.update(_normalize(a) for a in opt.aliases)
            if text in candidates:
                return opt.key
        return None

    def resolve_next(self, answer: str) -> str | None:
        return self.next(answer) if callable(self.next) else self.next


@dataclass
class ConversationState:
    phone: str
    flow: str
    step: str
    data: dict[str, str] = field(default_factory=dict)
    reprompts: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_expired(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return now - self.updated_at > STATE_TTL


class StateStore(Protocol):
    def get(self, phone: str) -> ConversationState | None: ...
    def save(self, state: ConversationState) -> None: ...
    def clear(self, phone: str) -> None: ...


class InMemoryStore:
    """Development store. Lost on restart; Phase 3 replaces it with Mongo."""

    def __init__(self) -> None:
        self._states: dict[str, ConversationState] = {}

    def get(self, phone: str) -> ConversationState | None:
        state = self._states.get(phone)
        if state is None:
            return None
        if state.is_expired():
            logger.info("conversation state expired")
            del self._states[phone]
            return None
        return state

    def save(self, state: ConversationState) -> None:
        state.updated_at = datetime.now(timezone.utc)
        self._states[state.phone] = state

    def clear(self, phone: str) -> None:
        self._states.pop(phone, None)


# --- the appointment flow. Add steps here; the engine does not change. ---

YES_NO = (
    Option("yes", "Yes", ("y", "yeah", "yep", "haan", "han", "ji", "ji haan")),
    Option("no", "No", ("n", "nope", "nahi", "nahin")),
)

APPOINTMENT_FLOW: dict[str, Step] = {
    "ask_returning": Step(
        id="ask_returning",
        question="Happy to help you book an appointment. Have you visited us before?",
        options=YES_NO,
        field="returning_patient",
        next=lambda answer: "ask_name" if answer == "no" else "ask_reason",
    ),
    "ask_name": Step(
        id="ask_name",
        question="Please share your full name so we can create your record.",
        field="name",
        next="ask_reason",
    ),
    "ask_reason": Step(
        id="ask_reason",
        question="What would you like to be seen for?",
        options=(
            Option("general", "General check-up"),
            Option("symptoms", "I'm feeling unwell"),
            Option("followup", "Follow-up visit"),
        ),
        field="reason",
        next=lambda answer: "ask_symptoms" if answer == "symptoms" else "ask_datetime",
    ),
    "ask_symptoms": Step(
        id="ask_symptoms",
        # free text here feeds the OpenAI extraction step, then the classifier
        question="Please describe what you're feeling, in your own words.",
        field="symptom_text",
        next="ask_datetime",
    ),
    "ask_datetime": Step(
        id="ask_datetime",
        question="What date and time would suit you best?",
        field="preferred_datetime",
        next=None,
    ),
}

FLOWS: dict[str, dict[str, Step]] = {"appointment": APPOINTMENT_FLOW}

FLOW_ENTRY_STEP = {"appointment": "ask_returning"}

# says a request was submitted, never that an appointment is booked
COMPLETION_MESSAGE = (
    "Thank you. We've passed your request to our staff, and they'll message "
    "you shortly to confirm your appointment."
)

CANCELLED_MESSAGE = (
    "No problem, I've stopped that. Message us anytime if you'd like to start "
    "again."
)

HANDOFF_MESSAGE = (
    "Sorry, I'm having trouble understanding. A member of our staff will "
    "message you shortly to help."
)


@dataclass(frozen=True)
class FlowResult:
    text: str
    step: str | None
    finished: bool = False
    data: dict[str, str] = field(default_factory=dict)


class ConversationEngine:
    def __init__(self, store: StateStore | None = None) -> None:
        self.store = store or InMemoryStore()

    def is_active(self, phone: str) -> bool:
        return self.store.get(phone) is not None

    def start(self, phone: str, flow: str) -> FlowResult:
        entry = FLOW_ENTRY_STEP[flow]
        state = ConversationState(phone=phone, flow=flow, step=entry)
        self.store.save(state)
        return FlowResult(text=FLOWS[flow][entry].render(), step=entry)

    def advance(self, phone: str, reply: str) -> FlowResult | None:
        """Read a reply as an answer to the current step.

        Returns None when the patient is not in a flow, so the caller falls
        through to its normal handling.
        """
        state = self.store.get(phone)
        if state is None:
            return None

        if _normalize(reply) in CANCEL_WORDS:
            self.store.clear(phone)
            return FlowResult(text=CANCELLED_MESSAGE, step=None, finished=True)

        step = FLOWS[state.flow][state.step]
        answer = step.match(reply)

        if answer is None:
            state.reprompts += 1
            if state.reprompts > MAX_REPROMPTS:
                logger.info("handing off to staff after repeated no-match")
                self.store.clear(phone)
                return FlowResult(text=HANDOFF_MESSAGE, step=None, finished=True)
            self.store.save(state)
            return FlowResult(
                text="Sorry, I didn't catch that.\n\n" + step.render(),
                step=state.step,
            )

        if step.field:
            state.data[step.field] = answer
        state.reprompts = 0

        next_id = step.resolve_next(answer)
        if next_id is None:
            data = dict(state.data)
            self.store.clear(phone)
            return FlowResult(
                text=COMPLETION_MESSAGE, step=None, finished=True, data=data
            )

        state.step = next_id
        self.store.save(state)
        return FlowResult(text=FLOWS[state.flow][next_id].render(), step=next_id)
