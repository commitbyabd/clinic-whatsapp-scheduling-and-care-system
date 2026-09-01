"""
Tests for the decision chain in orchestrator.py.

test_response.py pins down *which rule* a message hits. This file tests the
layers above it: which of the four sources answers, that the chain degrades
correctly when a component is missing, and that layer 2 stays inside the
clinic's safety rules.

Both models are stubbed throughout — these tests never touch the network, never
need an API key, and pass identically before and after the outsourced
classifier is delivered. That is the point of the seam.

No dependencies. Run either way:

    python tests/test_orchestrator.py     # today
    pytest                                # once pytest is installed
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from chatbot import classifier  # noqa: E402
from chatbot import llm_fallback  # noqa: E402
from chatbot import orchestrator  # noqa: E402
from chatbot.classifier import SPECIALIZATIONS, Classification  # noqa: E402
from chatbot.orchestrator import CANNED_REPLY, handle_message  # noqa: E402


class _StubLLM:
    """Swap out the OpenAI call for the duration of a test.

    Records what it was asked, so we can assert the model is never consulted
    for a message an earlier layer already answered — a silent cost leak,
    invisible except on the bill.
    """

    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def __call__(self, message):
        self.calls.append(message)
        return self.reply

    def __enter__(self):
        self._original = llm_fallback.generate_fallback_reply
        orchestrator.llm_fallback.generate_fallback_reply = self
        return self

    def __exit__(self, *exc):
        orchestrator.llm_fallback.generate_fallback_reply = self._original


class _StubClassifier:
    """Register a fake symptom classifier, then restore the empty registry.

    `result` may be a Classification, None, an Exception to raise, or malformed
    junk — the point is that every one of those degrades to the next layer.
    """

    def __init__(self, result):
        self.result = result
        self.calls = []

    def __call__(self, symptoms):
        self.calls.append(list(symptoms))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result

    def __enter__(self):
        self._original = classifier._classifier
        classifier.register(self)
        return self

    def __exit__(self, *exc):
        classifier._classifier = self._original


def _pred(specialization="Cardiologist", confidence=0.9):
    return Classification(specialization=specialization, confidence=confidence)


UNMATCHED = "do you have parking available?"
SYMPTOM_TEXT = "my chest feels tight when I walk up stairs"
SYMPTOMS = ["chest_pain", "breathlessness"]


# --- layer 1: rules -----------------------------------------------------


def test_rule_match_answers_without_calling_either_model():
    with _StubClassifier(_pred()) as clf, _StubLLM("unused") as llm:
        reply = handle_message("what are your timings", symptoms=SYMPTOMS)
    assert reply.source == "clinic_hours", reply.source
    assert reply.matched is True
    assert clf.calls == [], f"classifier called for a matched message: {clf.calls}"
    assert llm.calls == [], f"LLM called for a matched message: {llm.calls}"


def test_emergency_never_reaches_either_model():
    """The safety-critical path must not depend on any external service."""
    for message in ("I have severe chest pain", "my father is unconscious"):
        with _StubClassifier(_pred()) as clf, _StubLLM("unused") as llm:
            reply = handle_message(message, symptoms=SYMPTOMS)
        assert reply.source == "emergency", f"{message!r} -> {reply.source}"
        assert clf.calls == [] and llm.calls == [], f"model called for {message!r}"


# --- layer 2: classifier ------------------------------------------------


def test_classifier_answers_when_symptoms_are_supplied():
    with _StubClassifier(_pred()) as clf, _StubLLM("unused") as llm:
        reply = handle_message(SYMPTOM_TEXT, symptoms=SYMPTOMS)
    assert reply.source == "classifier"
    assert reply.classification.specialization == "Cardiologist"
    assert clf.calls == [SYMPTOMS], "classifier got the wrong input"
    assert llm.calls == [], "LLM was called even though the classifier answered"


def test_classifier_is_skipped_without_symptoms():
    """Today's behaviour: no extraction step, so layer 2 never runs."""
    with _StubClassifier(_pred()) as clf, _StubLLM("A general answer.") as llm:
        reply = handle_message(SYMPTOM_TEXT)
    assert reply.source == "llm"
    assert clf.calls == [], "classifier ran without extracted symptoms"
    assert llm.calls == [SYMPTOM_TEXT]


def test_classifier_output_changes_the_reply():
    """Phase 2 exit criterion: the classification must alter behaviour."""
    with _StubClassifier(_pred("Dermatologist")), _StubLLM(None):
        derm = handle_message(SYMPTOM_TEXT, symptoms=SYMPTOMS).text
    with _StubClassifier(_pred("Cardiologist")), _StubLLM(None):
        cardio = handle_message(SYMPTOM_TEXT, symptoms=SYMPTOMS).text
    assert "Dermatologist" in derm and "Cardiologist" in cardio
    assert derm != cardio, "specialization did not change the reply"


def test_every_valid_specialization_produces_a_reply():
    for spec in SPECIALIZATIONS:
        with _StubClassifier(_pred(spec)), _StubLLM(None):
            reply = handle_message(SYMPTOM_TEXT, symptoms=SYMPTOMS)
        assert reply.source == "classifier", f"{spec} was rejected"
        assert spec in reply.text


def test_unregistered_classifier_is_invisible():
    """The state the project is in today."""
    assert classifier.is_registered() is False
    with _StubLLM("A general answer.") as llm:
        reply = handle_message(SYMPTOM_TEXT, symptoms=SYMPTOMS)
    assert reply.source == "llm"
    assert llm.calls == [SYMPTOM_TEXT]


def test_classifier_failures_all_fall_through_to_the_llm():
    """Every way the outsourced model can misbehave degrades, none crash."""
    cases = {
        "returned None": None,
        "low confidence": _pred(confidence=0.1),
        "confidence as percent": _pred(confidence=87),
        "department the clinic lacks": _pred("Oncologist"),
        "returned a disease, not a specialization": _pred("Diabetes"),
        "wrong type entirely": {"specialization": "Cardiologist"},
        "raised": RuntimeError("model file missing"),
    }
    for label, result in cases.items():
        with _StubClassifier(result), _StubLLM("fallback answer"):
            reply = handle_message(SYMPTOM_TEXT, symptoms=SYMPTOMS)
        assert reply.source == "llm", f"{label} -> {reply.source}, expected llm"


def test_empty_symptom_list_skips_the_classifier():
    for empty in ([], [""], ["   "], None):
        with _StubClassifier(_pred()) as clf, _StubLLM("fallback"):
            reply = handle_message(SYMPTOM_TEXT, symptoms=empty)
        assert reply.source == "llm", f"{empty!r} -> {reply.source}"
        assert clf.calls == [], f"classifier called with {empty!r}"


# --- layer 2 safety -----------------------------------------------------


def test_classifier_replies_never_confirm_a_booking():
    """A receptionist confirms every booking — the bot must never imply one."""
    forbidden = (
        "you are booked",
        "you're booked",
        "is confirmed",
        "has been confirmed",
        "i have booked",
        "we have booked",
        "your appointment is",
    )
    for spec in SPECIALIZATIONS:
        with _StubClassifier(_pred(spec)):
            text = handle_message(SYMPTOM_TEXT, symptoms=SYMPTOMS).text.lower()
        for phrase in forbidden:
            assert phrase not in text, f"{spec}: said {phrase!r}"


def test_a_disease_name_can_never_reach_a_patient():
    """The model is trained on diseases; naming one to a patient is diagnosis."""
    for disease in ("Diabetes", "Malaria", "Hypertension", "Tuberculosis"):
        with _StubClassifier(_pred(disease)), _StubLLM("fallback answer"):
            reply = handle_message(SYMPTOM_TEXT, symptoms=SYMPTOMS)
        assert reply.source == "llm", f"{disease} was accepted as a specialization"
        assert disease.lower() not in reply.text.lower()


# --- layers 3 and 4 -----------------------------------------------------


def test_unmatched_falls_through_to_the_model():
    with _StubLLM("Parking is available on site.") as llm:
        reply = handle_message(UNMATCHED)
    assert reply.source == "llm"
    assert reply.text == "Parking is available on site."
    assert len(llm.calls) == 1


def test_canned_reply_when_everything_is_unavailable():
    with _StubLLM(None):
        reply = handle_message(UNMATCHED)
    assert reply.source == "canned"
    assert reply.text == CANNED_REPLY


def test_blank_model_reply_is_treated_as_unavailable():
    for empty in ("", "   "):
        with _StubLLM(empty):
            reply = handle_message(UNMATCHED)
        assert reply.source == "canned", f"{empty!r} -> {reply.source}"


def test_junk_input_never_raises():
    for junk in ("", "   ", "👍", "asdfghjkl"):
        with _StubLLM(None):
            reply = handle_message(junk)
        assert reply.text, f"{junk!r} produced an empty reply"
        assert reply.source == "canned"


def test_real_components_are_inert_without_a_key_or_model():
    """Unstubbed, as the project actually stands today: no network, no crash."""
    reply = handle_message(UNMATCHED)
    assert reply.source == "canned"
    assert reply.text == CANNED_REPLY


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
