"""
Tests for the scripted question flow.

Two things are being protected here. The obvious one is that the state machine
walks its steps correctly. The one that actually matters is that being mid-flow
can never swallow an emergency — a patient answering a menu is still a patient.

There is also a property test (test_menu_and_parser_cannot_drift) that checks
every option in every flow is reachable by its number, its label, and each of
its aliases. That is the bug this design exists to prevent: someone reorders a
menu, forgets the parser, and "2" quietly means the wrong thing.

No dependencies. Run either way:

    python tests/test_conversation.py
    pytest
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from chatbot import orchestrator  # noqa: E402
from chatbot.conversation import (  # noqa: E402
    CANCEL_WORDS,
    FLOWS,
    MAX_REPROMPTS,
    ConversationEngine,
    ConversationState,
    InMemoryStore,
    Step,
)
from chatbot.orchestrator import handle_message  # noqa: E402

_counter = iter(range(10_000))


def _phone() -> str:
    """A fresh number per test, so state never leaks between them."""
    return f"whatsapp:+92300{next(_counter):07d}"


def _say(phone, *messages):
    """Send messages in order, return the final Reply."""
    reply = None
    for message in messages:
        reply = handle_message(message, phone=phone)
    return reply


# --- the state machine --------------------------------------------------


def test_appointment_intent_starts_the_flow():
    reply = _say(_phone(), "I want to book an appointment")
    assert reply.source == "flow"
    assert "visited us before" in reply.text
    assert "1. Yes" in reply.text and "2. No" in reply.text


def test_happy_path_collects_every_answer():
    phone = _phone()
    reply = _say(
        phone,
        "book an appointment",
        "2",                       # no, first visit
        "Ahmed Khan",
        "2",                       # feeling unwell
        "my chest feels tight",
        "Tuesday 3pm",
    )
    assert reply.collected == {
        "returning_patient": "no",
        "name": "Ahmed Khan",
        "reason": "symptoms",
        "symptom_text": "my chest feels tight",
        "preferred_datetime": "Tuesday 3pm",
    }


def test_branching_differs_by_answer():
    """Returning patients skip the name step; first-timers do not."""
    returning = _say(_phone(), "appointment", "1")
    first_time = _say(_phone(), "appointment", "2")
    assert "seen for" in returning.text, "returning patient was asked for a name"
    assert "full name" in first_time.text, "first-timer was not asked for a name"


def test_number_label_and_alias_all_work():
    for answer in ("1", "Yes", "yes", "YES", "haan", "ji", "y", "yeah"):
        reply = _say(_phone(), "appointment", answer)
        assert "seen for" in reply.text, f"{answer!r} did not register as yes"
    for answer in ("2", "No", "nahi", "nope", "n"):
        reply = _say(_phone(), "appointment", answer)
        assert "full name" in reply.text, f"{answer!r} did not register as no"


def test_out_of_range_number_is_not_accepted():
    reply = _say(_phone(), "appointment", "7")
    assert "didn't catch that" in reply.text


def test_free_text_step_accepts_anything():
    reply = _say(_phone(), "appointment", "2", "Zainab Bibi")
    assert "seen for" in reply.text


def test_unrecognised_reply_reasks_then_hands_off():
    phone = _phone()
    _say(phone, "appointment")
    for attempt in range(MAX_REPROMPTS):
        reply = handle_message("what?", phone=phone)
        assert "didn't catch that" in reply.text, f"attempt {attempt + 1}"
    reply = handle_message("still no idea", phone=phone)
    assert "staff will message you" in reply.text
    assert orchestrator.engine.is_active(phone) is False, "flow was not cleared"


def test_cancel_words_exit_the_flow():
    for word in sorted(CANCEL_WORDS):
        phone = _phone()
        _say(phone, "appointment")
        reply = handle_message(word, phone=phone)
        assert "stopped that" in reply.text, f"{word!r} did not cancel"
        assert orchestrator.engine.is_active(phone) is False


def test_completion_never_claims_a_booking():
    """A receptionist confirms every booking."""
    reply = _say(
        _phone(), "appointment", "1", "1", "Tuesday 3pm"
    )
    text = reply.text.lower()
    for phrase in ("you are booked", "is confirmed", "has been confirmed"):
        assert phrase not in text, f"completion message said {phrase!r}"
    assert "confirm" in text, "should still say staff will confirm"


# --- the property that keeps menus honest -------------------------------


def test_menu_and_parser_cannot_drift():
    """Every option must be reachable by number, by label, and by each alias."""
    for flow_name, steps in FLOWS.items():
        for step in steps.values():
            if not step.options:
                continue
            rendered = step.render()
            for index, option in enumerate(step.options, 1):
                assert f"{index}. {option.label}" in rendered, (
                    f"{flow_name}/{step.id}: option {index} missing from menu"
                )
                assert step.match(str(index)) == option.key
                assert step.match(option.label) == option.key
                for alias in option.aliases:
                    assert step.match(alias) == option.key, (
                        f"{flow_name}/{step.id}: alias {alias!r} unreachable"
                    )


def test_every_next_step_exists():
    """A typo'd next-step id should fail here, not on a live patient."""
    for flow_name, steps in FLOWS.items():
        for step in steps.values():
            answers = [o.key for o in step.options] or ["anything"]
            for answer in answers:
                nxt = step.resolve_next(answer)
                assert nxt is None or nxt in steps, (
                    f"{flow_name}/{step.id} -> {nxt!r} does not exist"
                )


# --- safety -------------------------------------------------------------


def test_emergency_preempts_the_flow_at_every_step():
    """The property this whole design must not break."""
    replies = ["1", "Ahmed Khan", "2", "chest tightness"]
    for depth in range(len(replies) + 1):
        phone = _phone()
        _say(phone, "appointment", *replies[:depth])
        reply = handle_message("I have severe chest pain", phone=phone)
        assert reply.source == "emergency", f"swallowed at depth {depth}"
        assert "emergency room" in reply.text


def test_emergency_clears_the_flow():
    """Resuming 'what date suits you?' after an emergency reply is indefensible."""
    phone = _phone()
    _say(phone, "appointment", "1")
    handle_message("my father is unconscious", phone=phone)
    assert orchestrator.engine.is_active(phone) is False


def test_no_phone_disables_the_flow():
    """Stateless mode still works — the pre-flow behaviour is intact."""
    reply = handle_message("I want to book an appointment")
    assert reply.source == "appointment"
    assert "preferred date and time" in reply.text


# --- state lifetime -----------------------------------------------------


def test_expired_state_is_discarded():
    store = InMemoryStore()
    engine = ConversationEngine(store)
    phone = _phone()
    engine.start(phone, "appointment")

    stale = store.get(phone)
    stale.updated_at = datetime.now(timezone.utc) - timedelta(days=2)
    store._states[phone] = stale

    assert engine.is_active(phone) is False
    assert engine.advance(phone, "1") is None, "a stale flow was resumed"


def test_advance_returns_none_when_not_in_a_flow():
    engine = ConversationEngine(InMemoryStore())
    assert engine.advance(_phone(), "1") is None


def test_state_is_isolated_per_phone():
    a, b = _phone(), _phone()
    _say(a, "appointment", "2")          # a is at ask_name
    reply_b = _say(b, "appointment")     # b has just started
    assert "visited us before" in reply_b.text
    reply_a = handle_message("Ahmed Khan", phone=a)
    assert "seen for" in reply_a.text, "state leaked between patients"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {test.__name__}\n  {exc}\n")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failed}/{len(tests)} test functions passed")
    sys.exit(1 if failed else 0)
