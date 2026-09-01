"""
The scripted question flow: numbered menus and the state that makes them work.

THE PROBLEM THIS SOLVES
-----------------------
A patient replies "1". On its own that means nothing — it is only an answer if
you remember what you asked. So every incoming message is interpreted against
the patient's *current step*, and each answer moves them to the next one. That
is a finite state machine, keyed by phone number.

    ask_returning ──yes──> ask_reason ──> ask_datetime ──> done
                  ──no───> ask_name ────> ask_reason ──> ...

WHY THE MENU IS RENDERED FROM THE OPTIONS
-----------------------------------------
`Step.render()` builds the numbered list from the same Option objects that
`Step.match()` accepts. Writing the question text and the accepted answers
separately is the classic bug here: someone reorders the menu, forgets to update
the parser, and "2" silently means the wrong thing. Here they cannot drift —
there is one source of truth.

WHAT COUNTS AS AN ANSWER
------------------------
Real patients do not reply "1". They reply "1.", "Yes", "yes please", "haan",
"y", or a digit emoji. `Option.aliases` carries those, and matching is done on
normalised text. An unrecognised reply re-asks rather than guessing — but only
MAX_REPROMPTS times, so a confused patient reaches a human instead of a loop.

THE ESCAPE HATCH THAT MATTERS MOST
----------------------------------
Being mid-flow must never suppress an emergency. A patient halfway through
booking who types "chest pain" needs the emergency reply, not "please reply 1 or
2". The orchestrator checks the rules layer *before* consulting this module, so
that path stays open at every step. Do not "optimise" that ordering away.

STORAGE
-------
`InMemoryStore` is fine for development and the demo, and loses everything on
restart. Phase 3 swaps in a Mongo-backed store implementing the same three
methods — nothing else changes. State also expires (STATE_TTL), so a patient
returning next week starts fresh instead of resuming a forgotten conversation.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol

logger = logging.getLogger(__name__)

# After this many unrecognised replies at one step, hand off to staff rather
# than asking again. A patient stuck in a menu loop is a patient we have lost.
MAX_REPROMPTS = 2

# A flow older than this is abandoned, not resumed.
STATE_TTL = timedelta(hours=24)

# Words that always exit the flow, whatever step the patient is on.
CANCEL_WORDS = frozenset(
    {"cancel", "stop", "exit", "quit", "menu", "start over", "restart", "back"}
)

_PUNCTUATION = re.compile(r"[^\w\s]+")


def _normalize(text: str) -> str:
    return _PUNCTUATION.sub(" ", text.lower()).strip()


@dataclass(frozen=True)
class Option:
    """One menu choice.

    `key` is what the code stores and branches on; `label` is what the patient
    reads. Keeping them separate means you can reword a menu without breaking
    the branching logic that depends on the answer.
    """

    key: str
    label: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Step:
    id: str
    question: str
    # Empty options = a free-text answer (a name, a preferred date).
    options: tuple[Option, ...] = ()
    # Where the answer is stored in state.data.
    field: str = ""
    # Next step id, or a callable taking the answer and returning one.
    # None ends the flow.
    next: str | Callable[[str], str | None] | None = None

    def render(self) -> str:
        """The question as the patient sees it, menu included."""
        if not self.options:
            return self.question
        lines = [f"{i}. {opt.label}" for i, opt in enumerate(self.options, 1)]
        return self.question + "\n\n" + "\n".join(lines)

    def match(self, reply: str) -> str | None:
        """Interpret a reply as one of this step's options.

        Accepts the position number ("2"), the label ("No"), or any alias.
        Returns the Option.key, or None if nothing matched. Free-text steps
        accept anything non-empty.
        """
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
    """Development store. Phase 3 replaces this with Mongo, same interface."""

    def __init__(self) -> None:
        self._states: dict[str, ConversationState] = {}

    def get(self, phone: str) -> ConversationState | None:
        state = self._states.get(phone)
        if state is None:
            return None
        if state.is_expired():
            logger.info("conversation state expired for %s", phone)
            del self._states[phone]
            return None
        return state

    def save(self, state: ConversationState) -> None:
        state.updated_at = datetime.now(timezone.utc)
        self._states[state.phone] = state

    def clear(self, phone: str) -> None:
        self._states.pop(phone, None)


# --- the appointment flow ------------------------------------------------
# An illustration of the shape, not the final script. Add steps here; the
# engine does not change.

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
        # First-time patients need a name on file; returning ones we look up.
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
        # "symptoms" is the branch that will collect free text and hand it to
        # the OpenAI extraction step, then the classifier (ENG-1660).
        next=lambda answer: "ask_symptoms" if answer == "symptoms" else "ask_datetime",
    ),
    "ask_symptoms": Step(
        id="ask_symptoms",
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

# Sent when the flow completes. Says a request was submitted, never that an
# appointment is booked — a receptionist confirms every booking.
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
    """What the flow wants said, and whether the patient is still in it."""

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
        """Begin a flow and return its first question."""
        entry = FLOW_ENTRY_STEP[flow]
        state = ConversationState(phone=phone, flow=flow, step=entry)
        self.store.save(state)
        return FlowResult(text=FLOWS[flow][entry].render(), step=entry)

    def advance(self, phone: str, reply: str) -> FlowResult | None:
        """Interpret a reply against the patient's current step.

        Returns None when the patient is not in a flow, so the caller can fall
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
                logger.info("handing %s to staff after repeated no-match", phone)
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
