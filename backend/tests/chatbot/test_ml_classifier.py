"""Tests for the outsourced symptom model, as wired into the chatbot.

These load the real model (~1.5s), unlike the other chatbot tests.

    python tests/chatbot/test_ml_classifier.py
    pytest
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from chatbot import classifier  # noqa: E402
from chatbot.classifier import SPECIALIZATIONS, Classification  # noqa: E402
from chatbot.conversation import APPOINTMENT_FLOW, SYMPTOM_STEP  # noqa: E402
from chatbot.ml.adapter import (  # noqa: E402
    EMERGENCY_DISEASES,
    MODEL_PATH,
    SPECIALIZATION_MAP_PATH,
    SymptomExtractor,
    SymptomModelClassifier,
)
from chatbot.ml.predict import DiseaseModel, load_specialization_map  # noqa: E402
from chatbot.orchestrator import engine, handle_message  # noqa: E402

# loaded once; registered per test so nothing leaks into the other test files
_MODEL = DiseaseModel.load(MODEL_PATH)
_CLASSIFY = SymptomModelClassifier(_MODEL, load_specialization_map(SPECIALIZATION_MAP_PATH))
_EXTRACT = SymptomExtractor(_MODEL)

_phones = iter(range(10_000))


class _Registered:
    def __init__(self, classify=_CLASSIFY, extract=_EXTRACT):
        self.classify, self.extract = classify, extract

    def __enter__(self):
        self._saved = (classifier._classifier, classifier._extractor)
        classifier.register(self.classify)
        classifier.register_extractor(self.extract)

    def __exit__(self, *exc):
        classifier._classifier, classifier._extractor = self._saved


def _phone():
    return f"whatsapp:+92311{next(_phones):07d}"


def _book(phone, symptom_text):
    # 2 = first visit, then the name, then 2 = feeling unwell, which lands
    # on the symptom step
    for message in ("I want to book an appointment", "2", "Ahmed Khan", "2"):
        handle_message(message, phone=phone)
    return handle_message(symptom_text, phone=phone)


# --- the delivered files --------------------------------------------------


def test_mapping_only_uses_departments_the_clinic_has():
    with open(SPECIALIZATION_MAP_PATH, newline="", encoding="utf-8") as f:
        used = {row["Specialization"].strip() for row in csv.DictReader(f)}
    assert used <= set(SPECIALIZATIONS), f"unknown departments: {used - set(SPECIALIZATIONS)}"


def test_emergency_diseases_exist_in_the_model():
    # a retrained model that renames one would silently lose its emergency check
    missing = EMERGENCY_DISEASES - set(_MODEL.classes_)
    assert not missing, f"not in model: {missing}"


def test_symptom_step_exists_in_the_flow():
    assert SYMPTOM_STEP in APPOINTMENT_FLOW


# --- the heart attack fix -------------------------------------------------


def test_heart_attack_symptoms_are_an_emergency():
    result = _CLASSIFY(["sweating", "breathlessness", "vomiting"])
    assert result is not None and result.emergency, result


def test_brain_hemorrhage_symptoms_are_an_emergency():
    result = _CLASSIFY(["weakness of one body side", "slurred speech"])
    assert result is not None and result.emergency, result


def test_emergency_skips_the_confidence_threshold():
    # 0.45 is under min_confidence, which would discard a normal prediction
    possible_heart_attack = Classification("Cardiologist", 0.45, emergency=True)
    with _Registered(classify=lambda symptoms: possible_heart_attack):
        assert classifier.classify(["x", "y"]) == possible_heart_attack


def test_one_symptom_never_raises_an_emergency():
    # "sweating" alone scores 0.74 heart attack: too weak to send anyone to A&E,
    # and too risky to route as routine, so nothing comes back
    assert _CLASSIFY(["sweating"]) is None


def test_common_complaints_are_not_emergencies():
    for symptoms in (
        ["itching", "skin rash"],
        ["cough", "high fever", "chills"],
        ["vomiting", "diarrhoea"],
        ["back pain", "neck pain"],
        ["acidity", "indigestion", "headache"],
    ):
        result = _CLASSIFY(symptoms)
        assert result is None or not result.emergency, f"{symptoms} flagged as emergency"


def test_routine_symptoms_route_to_a_department():
    result = _CLASSIFY(["itching", "skin rash", "nodal skin eruptions"])
    assert result is not None and not result.emergency
    assert result.specialization == "Dermatologist"


# --- the extractor ----------------------------------------------------------


def test_extractor_reads_plain_sentences():
    cases = {
        "my skin is really itchy and I have a rash": ["itching", "skin_rash"],
        "I have had a bad hedache and been throwing up": ["headache", "vomiting"],
        "I am sweating a lot, short of breath and throwing up": [
            "sweating", "breathlessness", "vomiting",
        ],
    }
    for text, expected in cases.items():
        assert _EXTRACT(text) == expected, f"{text!r} -> {_EXTRACT(text)}"


def test_extractor_drops_denied_symptoms():
    # a denied symptom must not add up to a false heart attack
    assert _EXTRACT("I am not sweating and have no fever, just a cough") == ["cough"]
    assert _EXTRACT("no fever or cough") == []


def test_negation_stops_at_the_end_of_a_clause():
    text = "not sweating, no breathlessness, just itchy skin and a rash"
    assert _EXTRACT(text) == ["itching", "skin_rash"]


def test_cant_breathe_is_a_symptom_not_a_denial():
    assert _EXTRACT("I cant breathe and I cant sleep") == ["breathlessness", "restlessness"]


# --- in the booking flow ----------------------------------------------------


def test_booking_stops_for_a_heart_attack_described_without_keywords():
    phone = _phone()
    with _Registered():
        reply = _book(phone, "I am sweating a lot, short of breath and throwing up")
    assert reply.source == "emergency", reply.source
    # set only by the classifier path, so this proves the rules layer did not
    # catch it first and pass the test for the wrong reason
    assert reply.classification is not None and reply.classification.emergency
    assert engine.is_active(phone) is False, "booking was not stopped"


def test_booking_names_the_department_and_passes_it_on():
    phone = _phone()
    with _Registered():
        reply = _book(phone, "my skin is really itchy and I have a rash with blisters")
        assert "Dermatologist" in reply.text, reply.text
        done = handle_message("Tuesday 3pm", phone=phone)
    assert done.collected["specialization"] == "Dermatologist", done.collected


def test_booking_carries_on_when_symptoms_are_too_vague():
    phone = _phone()
    with _Registered():
        reply = _book(phone, "I have been sweating a lot")
    assert reply.source == "flow" and reply.classification is None
    assert "date and time" in reply.text


def test_booking_works_without_the_model():
    # the state before the model existed, and what happens if it fails to load
    phone = _phone()
    with _Registered(classify=None, extract=None):
        classifier._classifier = classifier._extractor = None
        reply = _book(phone, "I am sweating a lot, short of breath and throwing up")
    assert reply.source == "flow" and "date and time" in reply.text


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
