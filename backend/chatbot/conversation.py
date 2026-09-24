"""Scripted question flow: numbered menus and the per-patient state behind them.

A reply like "1" only means something if you remember what was asked, so each
phone number gets a state machine tracking which step it is on.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol

from chatbot import directory

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
    # Worked out when the flow reaches the step, from what the patient has
    # said so far: the doctors in their department, a doctor's open times.
    # The question and choices it comes up with are kept in the state, so a
    # reply of "2" still means what the patient saw. See Prepared.
    prepare: Callable[[ConversationState], Prepared] | None = None

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
    # for a prepared step: what was asked, and the [key, label] choices shown
    question: str = ""
    choices: list[list[str]] = field(default_factory=list)

    def is_expired(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return now - self.updated_at > STATE_TTL


class StateStore(Protocol):
    def get(self, phone: str) -> ConversationState | None: ...
    def save(self, state: ConversationState) -> None: ...
    def clear(self, phone: str) -> None: ...


class InMemoryStore:
    """Used by the tests, and until startup puts the Mongo store in its place
    (app/features/whatsapp/v1/conversation_store.py). Lost on restart."""

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

# the orchestrator classifies the answer to this step, and reads symptoms typed
# at REASON_STEP instead of a menu number, so renaming either here means
# renaming it there
SYMPTOM_STEP = "ask_symptoms"
REASON_STEP = "ask_reason"

YES_NO = (
    Option("yes", "Yes", ("y", "yeah", "yep", "haan", "han", "ji", "ji haan")),
    Option("no", "No", ("n", "nope", "nahi", "nahin")),
)

DOCTOR_STEP = "choose_doctor"
TIME_STEP = "choose_time"
# the old free-text question, for when there is no doctor or time to offer
FREE_TIME_STEP = "ask_datetime"

NONE_OF_THESE = "none"
OPEN_TIMES_SHOWN = 6


@dataclass(frozen=True)
class Prepared:
    """What a step's prepare() decided, one of:

    question, choices   ask this, with these numbered (key, label) choices
    goto                skip the question and carry on at this step
    finish              end the chat with this text, sending no request

    answers are recorded whichever it is (the doctor picked, say), and note
    is put in front of whatever is said next.
    """

    question: str = ""
    choices: tuple[tuple[str, str], ...] = ()
    goto: str | None = None
    finish: str | None = None
    answers: dict[str, str] = field(default_factory=dict)
    note: str = ""


def _doctor_label(doctor: directory.Doctor) -> str:
    label = f"{doctor.name}, {doctor.specialization}"
    return f"{label} (walk-in)" if doctor.walk_in else label


def _doctor_menu(doctors: list[directory.Doctor], question: str, note: str) -> Prepared:
    # only one to choose from: take it rather than ask
    if len(doctors) == 1:
        return Prepared(answers={"doctor_id": doctors[0].id}, goto=TIME_STEP, note=note)
    return Prepared(
        question=question,
        choices=tuple((doctor.id, _doctor_label(doctor)) for doctor in doctors),
        note=note,
    )


def prepare_doctor(state: ConversationState) -> Prepared:
    """The doctors in the department the model suggested, or every doctor
    when there is no suggestion or nobody works in that department."""
    department = state.data.get("specialization")
    note = ""

    if department:
        doctors = directory.find_doctors(department)
        if doctors is None:
            return Prepared(goto=FREE_TIME_STEP)
        if doctors:
            return _doctor_menu(doctors, f"Which {department} would you like to see?", note)
        note = f"We don't have a {department} at the moment."

    doctors = directory.find_doctors()
    if not doctors:
        # no directory, it failed, or no doctor has working hours yet
        return Prepared(goto=FREE_TIME_STEP, note=note)
    return _doctor_menu(doctors, "Which doctor would you like to see?", note)


def prepare_time(state: ConversationState) -> Prepared:
    """A walk-in doctor's hours end the chat; an appointment doctor's next
    open times become the choices."""
    doctor = directory.find_doctor(state.data.get("doctor_id", ""))
    if doctor is None:
        return Prepared(goto=FREE_TIME_STEP)

    answers = {"doctor_name": doctor.name}
    hours = directory.describe_hours(doctor.hours)

    # first come, first served: nothing to book, so nothing goes to reception
    if doctor.walk_in:
        return Prepared(
            answers=answers,
            finish=(
                f"{doctor.name} ({doctor.specialization}) sees patients on a "
                f"first-come, first-served basis: {hours}. No appointment is "
                "needed, just come in during these hours."
            ),
        )

    times = directory.find_open_times(doctor.id, OPEN_TIMES_SHOWN)
    if not times:
        note = (
            f"{doctor.name} has no open times in the next two weeks."
            if times == []
            else ""
        )
        return Prepared(answers=answers, goto=FREE_TIME_STEP, note=note)

    # The patient asks for a time; nothing is held. A receptionist still
    # confirms it, and may offer another if it has gone in the meantime.
    return Prepared(
        answers=answers,
        question=(
            f"{doctor.name} ({doctor.specialization}) sees patients {hours}.\n\n"
            "Reply with a number to ask for one of these times:"
        ),
        choices=tuple(
            (moment.isoformat(), directory.slot_label(moment)) for moment in times
        )
        + ((NONE_OF_THESE, "None of these"),),
    )


APPOINTMENT_FLOW: dict[str, Step] = {
    "ask_returning": Step(
        id="ask_returning",
        question="Happy to help you book an appointment. Have you visited us before?",
        options=YES_NO,
        field="returning_patient",
        # Both are asked for a name: a first-timer's creates the record, and a
        # returning patient's lets reception find theirs among the family
        # members who share the phone.
        next=lambda answer: "ask_name" if answer == "no" else "ask_returning_name",
    ),
    "ask_name": Step(
        id="ask_name",
        question="Please share your full name so we can create your record.",
        field="name",
        next="ask_reason",
    ),
    "ask_returning_name": Step(
        id="ask_returning_name",
        question="Welcome back. Please share the patient's full name so we can find the record.",
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
        next=lambda answer: "ask_symptoms" if answer == "symptoms" else DOCTOR_STEP,
    ),
    "ask_symptoms": Step(
        id="ask_symptoms",
        # free text here feeds the OpenAI extraction step, then the classifier
        question="Please describe what you're feeling, in your own words.",
        field="symptom_text",
        next=DOCTOR_STEP,
    ),
    DOCTOR_STEP: Step(
        id=DOCTOR_STEP,
        question="Which doctor would you like to see?",
        field="doctor_id",
        next=TIME_STEP,
        prepare=prepare_doctor,
    ),
    TIME_STEP: Step(
        id=TIME_STEP,
        question="Which time would suit you?",
        field="requested_slot",
        next=lambda answer: FREE_TIME_STEP if answer == NONE_OF_THESE else None,
        prepare=prepare_time,
    ),
    FREE_TIME_STEP: Step(
        id=FREE_TIME_STEP,
        question="What date and time would suit you best?",
        field="preferred_datetime",
        next=None,
    ),
}

# --- the booking offer, sent when a patient describes symptoms unprompted ---

OFFER_FLOW = "offer"

BOOKING_YES_NO = (
    Option(
        "yes",
        "Yes",
        ("y", "yeah", "yep", "sure", "ok", "okay", "yes please", "please",
         "haan", "han", "ji", "ji haan", "theek hai"),
    ),
    Option("no", "No", ("n", "nope", "no thanks", "not now", "later", "nahi", "nahin")),
)

OFFER_STEPS: dict[str, Step] = {
    "ask_book": Step(
        id="ask_book",
        question="Would you like to book an appointment?",
        options=BOOKING_YES_NO,
        field="wants_booking",
        next=None,
    ),
}

FLOWS: dict[str, dict[str, Step]] = {
    "appointment": APPOINTMENT_FLOW,
    OFFER_FLOW: OFFER_STEPS,
}

FLOW_ENTRY_STEP = {"appointment": "ask_returning", OFFER_FLOW: "ask_book"}

# says a request was submitted, never that an appointment is booked
COMPLETION_MESSAGE = (
    "Thank you. We've passed your request to our staff, and they'll message "
    "you shortly to confirm your appointment."
)


def completion_message(data: dict[str, str]) -> str:
    """Names the time and doctor asked for, when there are some. Still a
    request: a receptionist confirms it."""
    slot = data.get("requested_slot", "")
    doctor = data.get("doctor_name")
    if not doctor or not slot or slot == NONE_OF_THESE:
        return COMPLETION_MESSAGE
    try:
        when = directory.slot_label(datetime.fromisoformat(slot))
    except ValueError:
        return COMPLETION_MESSAGE
    return (
        f"Thank you. We've passed your request for {when} with {doctor} to our "
        "staff, and they'll message you shortly to confirm your appointment."
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

    def start(
        self, phone: str, flow: str, answers: dict[str, str] | None = None
    ) -> FlowResult:
        """Begin a flow. answers holds anything the patient already told us."""
        entry = FLOW_ENTRY_STEP[flow]
        state = ConversationState(
            phone=phone, flow=flow, step=entry, data=dict(answers or {})
        )
        return self._move_to(state, entry)

    def understands(self, phone: str, reply: str) -> bool:
        """True when advance() would take the reply as an answer or a cancel."""
        state = self.store.get(phone)
        if state is None:
            return False
        if _normalize(reply) in CANCEL_WORDS:
            return True
        return self._step(state).match(reply) is not None

    def current_prompt(self, phone: str) -> str | None:
        """The question the patient is on, asked again: after answering
        something they asked in between, say."""
        state = self.store.get(phone)
        return None if state is None else self._step(state).render()

    def fill(self, phone: str, answers: dict[str, str]) -> FlowResult | None:
        """Record answers given early, then ask the next question still open."""
        state = self.store.get(phone)
        if state is None:
            return None
        state.data.update(answers)
        state.reprompts = 0
        return self._move_to(state, state.step)

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

        step = self._step(state)
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
        return self._move_to(state, step.resolve_next(answer))

    def _step(self, state: ConversationState) -> Step:
        """The current step as the patient saw it. A prepared step carries the
        question and choices worked out for them, kept in the state."""
        step = FLOWS[state.flow][state.step]
        if step.prepare is None:
            return step
        return replace(
            step,
            question=state.question,
            options=tuple(Option(key, label) for key, label in state.choices),
        )

    def _move_to(self, state: ConversationState, step_id: str | None) -> FlowResult:
        steps = FLOWS[state.flow]
        notes: list[str] = []

        # Bounded, so a flow that loops cannot hang here: each pass asks,
        # finishes, or moves on to another step.
        for _ in range(2 * len(steps)):
            if step_id is None:
                break
            step = steps[step_id]

            # skip questions already answered, e.g. symptoms described before
            # the flow asked for them
            if step.field in state.data:
                step_id = step.resolve_next(state.data[step.field])
                continue

            if step.prepare is None:
                state.question, state.choices = "", []
                break

            prepared = step.prepare(state)
            state.data.update(prepared.answers)
            if prepared.note:
                notes.append(prepared.note)

            if prepared.finish is not None:
                # nothing to request, so the flow ends without data
                self.store.clear(state.phone)
                return FlowResult(
                    text=_joined(notes, prepared.finish), step=None, finished=True
                )

            if prepared.goto is not None:
                step_id = prepared.goto
                continue

            state.question = prepared.question
            state.choices = [[key, label] for key, label in prepared.choices]
            break

        if step_id is None:
            data = dict(state.data)
            self.store.clear(state.phone)
            return FlowResult(
                text=_joined(notes, completion_message(data)),
                step=None,
                finished=True,
                data=data,
            )

        state.step = step_id
        self.store.save(state)
        return FlowResult(text=_joined(notes, self._step(state).render()), step=step_id)


def _joined(notes: list[str], text: str) -> str:
    return "\n\n".join([*notes, text])
