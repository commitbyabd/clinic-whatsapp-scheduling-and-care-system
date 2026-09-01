"""
Tests for the response matcher.

These exist mainly to catch ORDERING regressions in rules.py. The rules are
evaluated first-match-wins, so adding a keyword to one rule can silently steal
messages from another — the cases below pin down the intent each message
should resolve to.

No dependencies. Run either way:

    python tests/test_response.py     # today
    pytest                            # once pytest is installed
"""

import sys
from pathlib import Path

# Put the project root on the path so the package resolves whether this is run
# directly or collected by pytest.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from chatbot.predefined_responses import clinic  # noqa: E402
from chatbot.predefined_responses.response import (  # noqa: E402
    RULES,
    match_response,
    match_rule,
)

# (message, expected rule name or None)
CASES: list[tuple[str, str | None]] = [
    # --- regressions: each of these resolved to the wrong rule before ---
    ("Hi, I want to book an appointment", "appointment"),
    ("Hello, what time do you open?", "clinic_hours"),
    ("Thanks, can I reschedule?", "appointment_cancel"),
    ("Salam, how much is the fee?", "fees"),
    ("take care", "farewell"),
    ("I don't care about that", None),
    ("can you open a file for me", None),
    ("where do I send my report?", None),
    ("I don't want to cancel, just confirm", "appointment_confirm"),
    ("I want customer service", "human_agent"),
    ("which doctor is available", "doctor_info"),
    # --- inflections that used to fall through ---
    ("is my appointment confirmed", "appointment_confirm"),
    ("I have booked already", "appointment"),
    ("cancelled my slot", "appointment_cancel"),
    ("do you offer check-ups", "services"),
    # --- small talk still works on its own ---
    ("hi", "greeting"),
    ("Hi!", "greeting"),
    ("HELLO 👋", "greeting"),
    ("hi there", "greeting"),
    ("hello doctor", "greeting"),
    ("thanks", "farewell"),
    ("thank you so much", "farewell"),
    ("thanks a lot", "farewell"),
    ("Assalamualaikum", "greeting"),
    ("jazakallahu khairan", "farewell"),
    ("jazakallah", "farewell"),
    ("shukriya", "farewell"),
    # --- safety always wins ---
    ("hi, I have severe chest pain", "emergency"),
    ("thanks but this is urgent", "emergency"),
    ("my father is unconscious", "emergency"),
    ("I need an ambulance", "emergency"),
    # --- word boundaries hold ---
    ("this will be fine", None),
    ("I will come", None),
    # --- ordinary intents ---
    ("what are your timings", "clinic_hours"),
    ("are you open tomorrow", "clinic_hours"),
    ("where is the clinic", "location"),
    ("what is your address", "location"),
    ("what services do you have", "services"),
    ("consultation fee please", "fees"),
    ("how much for a checkup", "fees"),
    ("is it covered by insurance", "insurance"),
    ("give me your phone number", "contact"),
    ("I want to talk to someone", "human_agent"),
    ("help", "help"),
    ("what can you do", "help"),
    ("I have a fever and cough", "feeling_unwell"),
    ("not feeling well", "feeling_unwell"),
    # --- empty / junk ---
    ("", None),
    ("   ", None),
    ("👍", None),
    ("asdfghjkl", None),
]


def test_messages_resolve_to_expected_rule():
    failures = []
    for message, expected in CASES:
        result = match_rule(message)
        actual = result[0] if result else None
        if actual != expected:
            failures.append(f"  {message!r}: expected {expected}, got {actual}")
    assert not failures, "wrong rule matched:\n" + "\n".join(failures)


def test_every_keyword_matches_its_own_pattern():
    """A keyword that cannot match itself is dead config — usually a stray
    capital, or a word-boundary problem like 'check-up' vs 'check-ups'."""
    for name, rule in RULES.items():
        for keyword in rule["keywords"]:
            assert rule["pattern"].search(keyword), f"{name}: {keyword!r} is unreachable"
            assert keyword == keyword.lower(), f"{name}: {keyword!r} is not lower-case"


def test_no_rule_is_fully_shadowed():
    """Every rule must be reachable: at least one of its keywords has to
    survive the rules above it, or the rule is dead weight."""
    for name, rule in RULES.items():
        reachable = any(
            (match_rule(keyword) or (None,))[0] == name
            for keyword in rule["keywords"]
        )
        assert reachable, f"{name}: every keyword is claimed by an earlier rule"


def test_match_response_contract():
    assert match_response("hi") == RULES["greeting"]["response"]
    assert match_response("asdfghjkl") is None
    assert match_response("") is None


def test_responses_use_clinic_config():
    """Clinic facts must come from clinic.py, not be hardcoded in rules.py."""
    assert clinic.ADDRESS in RULES["location"]["response"]
    assert clinic.PHONE in RULES["contact"]["response"]
    assert clinic.EMAIL in RULES["contact"]["response"]
    assert clinic.OPENING_TIME in RULES["clinic_hours"]["response"]
    assert clinic.EMERGENCY_NUMBER in RULES["emergency"]["response"]


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {test.__name__}\n{exc}\n")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failed}/{len(tests)} test functions passed "
          f"({len(CASES)} message cases)")
    sys.exit(1 if failed else 0)
