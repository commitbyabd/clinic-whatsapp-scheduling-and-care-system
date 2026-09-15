"""
Tests for how adapter.py turns the model's probabilities into a decision.

A fake model stands in for model.joblib, so these run without loading it, even
where scikit-learn cannot load at all. test_ml_classifier.py covers the real
model.

    python tests/chatbot/test_model_adapter.py
    pytest
"""

import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from chatbot.ml import adapter  # noqa: E402
from chatbot.settings import classifier_settings  # noqa: E402

CLASSES = ["Heart attack", "Paralysis (brain hemorrhage)", "Impetigo"]
MAPPING = {
    "Heart attack": "Cardiologist",
    "Paralysis (brain hemorrhage)": "Neurologist",
    "Impetigo": "Dermatologist",
}
# pinned, so an .env with different values cannot change what these check
SETTINGS = replace(classifier_settings, min_symptoms=2, emergency_threshold=0.4)


class _FakeModel:
    def __init__(self, heart_attack=0.0, department=("Dermatologist", 0.9), known=True):
        self.classes_ = CLASSES
        self._proba = [heart_attack, 0.0, 1.0 - heart_attack]
        self._department = department
        self.vocab = SimpleNamespace(
            resolve_many=lambda raws: [
                SimpleNamespace(ok=known, matched=raw if known else None) for raw in raws
            ]
        )

    def predict_proba_sets(self, sets):
        return [self._proba]

    def predict_specializations(self, recognized, mapping, top_k=1):
        name, probability = self._department
        return [SimpleNamespace(specialization=name, probability=probability)]


def _classify(symptoms, **model):
    saved = adapter.classifier_settings
    adapter.classifier_settings = SETTINGS
    try:
        return adapter.SymptomModelClassifier(_FakeModel(**model), MAPPING)(symptoms)
    finally:
        adapter.classifier_settings = saved


def test_one_clear_symptom_suggests_a_department():
    result = _classify(["blister"])
    assert result is not None and result.specialization == "Dermatologist", result
    assert result.emergency is False


def test_one_symptom_never_raises_an_emergency():
    # "sweating" alone scores 0.74 heart attack: too thin for an alarm, and too
    # risky to route as routine, so nothing comes back
    assert _classify(["sweating"], heart_attack=0.74) is None


def test_two_symptoms_can_raise_an_emergency():
    result = _classify(["sweating", "vomiting"], heart_attack=0.74)
    assert result is not None and result.emergency, result
    assert result.specialization == "Cardiologist"


def test_unrecognised_symptoms_are_ignored():
    assert _classify(["not_a_symptom"], known=False) is None


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
