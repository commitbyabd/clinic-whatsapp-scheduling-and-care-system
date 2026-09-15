"""
Tests for the OpenAI symptom extractor.

OpenAI is replaced by a fake client throughout, so these send nothing, cost
nothing and need no key or network. They pin down what the booking flow relies
on: only known symptom names come back, and any failure hands the message to
the keyword matcher instead of losing it.

    python tests/chatbot/test_symptom_extraction.py
    pytest
"""

import logging
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import openai  # noqa: E402

from chatbot import classifier  # noqa: E402
from chatbot.settings import classifier_settings, openai_settings  # noqa: E402
from chatbot.symptom_extraction import OpenAISymptomExtractor  # noqa: E402

KNOWN = ["chest_pain", "sweating", "vomiting", "itching"]
SETTINGS = replace(openai_settings, api_key="sk-test-not-real", model="test-model")
PATIENT = "my chest feels tight and I keep sweating"


class _FakeClient:
    """Stands in for OpenAI: records each request, then answers or raises."""

    def __init__(self, content=None, error=None):
        self.content = content
        self.error = error
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        message = SimpleNamespace(content=self.content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class _Keywords:
    """The backup matcher, recording whether it was used."""

    def __init__(self, result=("vomiting",)):
        self.result = list(result)
        self.calls = []

    def __call__(self, text):
        self.calls.append(text)
        return self.result


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(self.format(record))


def _extractor(client, keywords=None):
    return OpenAISymptomExtractor(
        KNOWN, fallback=keywords or _Keywords(), client=client, settings=SETTINGS
    )


# --- what comes back --------------------------------------------------------


def test_reads_the_symptom_list_from_the_answer():
    client = _FakeClient('{"symptoms": ["chest_pain", "sweating"]}')
    assert _extractor(client)(PATIENT) == ["chest_pain", "sweating"]


def test_an_empty_list_is_trusted():
    # "nothing matched" is an answer, not a failure, so keywords are not asked
    keywords = _Keywords()
    client = _FakeClient('{"symptoms": []}')
    assert _extractor(client, keywords)("I want to book for my mother") == []
    assert keywords.calls == []


def test_unknown_names_are_dropped():
    client = _FakeClient('{"symptoms": ["chest_pain", "chest_tightness"]}')
    assert _extractor(client)(PATIENT) == ["chest_pain"]


def test_duplicates_are_removed_in_order():
    client = _FakeClient('{"symptoms": ["sweating", "chest_pain", "sweating"]}')
    assert _extractor(client)(PATIENT) == ["sweating", "chest_pain"]


# --- what is sent -----------------------------------------------------------


def test_answers_are_limited_to_the_known_names():
    client = _FakeClient('{"symptoms": []}')
    _extractor(client)(PATIENT)
    schema = client.requests[0]["response_format"]["json_schema"]
    assert schema["strict"] is True
    items = schema["schema"]["properties"]["symptoms"]["items"]
    assert items["enum"] == sorted(KNOWN), items


def test_the_patient_message_is_sent_as_the_user_turn():
    client = _FakeClient('{"symptoms": []}')
    _extractor(client)(PATIENT)
    messages = client.requests[0]["messages"]
    assert messages[0]["role"] == "system"
    assert messages[-1] == {"role": "user", "content": PATIENT}


def test_a_blank_message_is_not_sent():
    client = _FakeClient('{"symptoms": ["sweating"]}')
    extract = _extractor(client)
    assert extract("") == [] and extract("   ") == []
    assert client.requests == []


# --- failures fall back to keywords -----------------------------------------


def test_an_openai_error_uses_keywords():
    keywords = _Keywords(["vomiting"])
    client = _FakeClient(error=openai.OpenAIError("simulated outage"))
    assert _extractor(client, keywords)(PATIENT) == ["vomiting"]
    assert keywords.calls == [PATIENT]


def test_an_unusable_answer_uses_keywords():
    # None is what a refusal looks like
    for content in ("not json", None, '{"wrong_key": []}', '{"symptoms": "sweating"}'):
        keywords = _Keywords(["vomiting"])
        result = _extractor(_FakeClient(content), keywords)(PATIENT)
        assert result == ["vomiting"], f"{content!r} -> {result}"


def test_an_unexpected_crash_uses_keywords():
    keywords = _Keywords(["vomiting"])
    client = _FakeClient(error=RuntimeError("simulated bug"))
    assert _extractor(client, keywords)(PATIENT) == ["vomiting"]


def test_the_patient_message_is_never_logged():
    logger = logging.getLogger("chatbot.symptom_extraction")
    capture = _Capture()
    logger.addHandler(capture)
    try:
        for error in (openai.OpenAIError("simulated"), RuntimeError("simulated")):
            _extractor(_FakeClient(error=error))(PATIENT)
        _extractor(_FakeClient("not json"))(PATIENT)
    finally:
        logger.removeHandler(capture)
    logged = "\n".join(capture.lines)
    assert capture.lines, "nothing was logged, so this proves nothing"
    assert "chest" not in logged and "sweating" not in logged, logged


# --- plugged into the chatbot -----------------------------------------------


def test_the_classifier_seam_uses_it():
    saved = classifier._extractor
    classifier.register_extractor(_extractor(_FakeClient('{"symptoms": ["itching"]}')))
    try:
        assert classifier.extract_symptoms("my skin is so itchy") == ["itching"]
    finally:
        classifier._extractor = saved


class _FakeVocab:
    def __init__(self, symptoms):
        self.symptoms = list(symptoms)
        self.synonyms = {}
        self.index = {s: i for i, s in enumerate(self.symptoms)}

    def __len__(self):
        return len(self.symptoms)


def test_startup_uses_openai_only_when_it_is_set_up():
    # a fake model, so this runs without loading the real one
    from chatbot.ml import adapter

    model = SimpleNamespace(
        classes_=["Heart attack", "Paralysis (brain hemorrhage)"],
        vocab=_FakeVocab(KNOWN),
    )
    saved = (
        adapter.DiseaseModel, adapter.load_specialization_map,
        adapter.classifier_settings, adapter.openai_settings,
        classifier._classifier, classifier._extractor,
    )
    adapter.DiseaseModel = SimpleNamespace(load=lambda path: model)
    adapter.load_specialization_map = lambda path: {"Heart attack": "Cardiologist"}
    adapter.classifier_settings = replace(classifier_settings, enabled=True)
    try:
        cases = [
            (replace(SETTINGS, extraction_enabled=True), OpenAISymptomExtractor),
            (replace(SETTINGS, extraction_enabled=False), adapter.SymptomExtractor),
            (replace(SETTINGS, api_key=""), adapter.SymptomExtractor),
        ]
        for settings, expected in cases:
            adapter.openai_settings = settings
            adapter.register_symptom_model()
            assert isinstance(classifier._extractor, expected), (settings, classifier._extractor)
    finally:
        (
            adapter.DiseaseModel, adapter.load_specialization_map,
            adapter.classifier_settings, adapter.openai_settings,
            classifier._classifier, classifier._extractor,
        ) = saved


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
