"""Adapter between the outsourced symptom model and chatbot/classifier.py.

predict.py, model.joblib and the mapping CSV are kept exactly as delivered, so a
retrained model can be dropped straight in. Anything specific to this clinic,
including which diseases count as emergencies, lives here instead.
"""

from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher
from pathlib import Path

from chatbot import classifier
from chatbot.classifier import Classification
from chatbot.ml.predict import DiseaseModel, load_specialization_map, normalize
from chatbot.settings import classifier_settings, openai_settings
from chatbot.symptom_extraction import OpenAISymptomExtractor

logger = logging.getLogger(__name__)

ML_DIR = Path(__file__).resolve().parent
MODEL_PATH = ML_DIR / "model.joblib"
SPECIALIZATION_MAP_PATH = ML_DIR / "disease_specialization_mapping.csv"

# the reply for these must be "get help now", never "book an appointment".
# add to this rather than lowering the threshold.
EMERGENCY_DISEASES = frozenset({"Heart attack", "Paralysis (brain hemorrhage)"})

# "cant" is deliberately missing: "cant breathe" and "cant sleep" are symptoms
_NEGATIONS = frozenset({
    "no", "not", "never", "without", "nor",
    "dont", "doesnt", "didnt", "isnt", "arent", "wasnt", "havent", "hasnt",
})
_NEGATION_WINDOW = 3
_MAX_NGRAM = 4
_FUZZY_MIN_LENGTH = 6
_FUZZY_CUTOFF = 0.85
_WORD = re.compile(r"[a-z]+")
# negation stops at these, so the "no" in "no fever, just a cough" cannot
# reach forward and cancel the cough. "and"/"or" are not breaks: "no fever or
# cough" denies both.
_CLAUSE_BREAK = re.compile(
    r"[.,;:!?\n]|\b(?:but|just|however|though|although|except|only)\b"
)


class SymptomModelClassifier:
    def __init__(self, model: DiseaseModel, specialization_map: dict[str, str]):
        self.model = model
        self.specialization_map = specialization_map
        self._emergency = [
            (i, d) for i, d in enumerate(model.classes_) if d in EMERGENCY_DISEASES
        ]
        missing = EMERGENCY_DISEASES - set(model.classes_)
        if missing:
            # a retrained model that renamed one of these would silently lose
            # its emergency check, so make it loud
            logger.error("emergency diseases missing from model: %s", sorted(missing))

    def __repr__(self) -> str:
        return "SymptomModelClassifier"

    def __call__(self, symptoms) -> Classification | None:
        recognized = [m.matched for m in self.model.vocab.resolve_many(symptoms) if m.ok]
        if not recognized:
            return None
        # fewer than this is too thin to raise an alarm on: "sweating" alone
        # scores 0.74 heart attack. It can still suggest a department, since
        # most symptoms belong to one department (blister -> Dermatologist).
        enough = len(recognized) >= classifier_settings.min_symptoms

        proba = self.model.predict_proba_sets([frozenset(recognized)])[0]

        # checked before routing, and against the probability of the emergency
        # itself rather than the top prediction: "breathlessness, chest pain"
        # can rank pneumonia first while still being a likely heart attack
        worst = max(self._emergency, key=lambda e: proba[e[0]], default=None)
        if worst is not None and proba[worst[0]] >= classifier_settings.emergency_threshold:
            if not enough:
                # too thin for an alarm, too risky to route as routine
                return None
            index, disease = worst
            return Classification(
                specialization=self.specialization_map.get(disease, "General Physician"),
                confidence=min(1.0, float(proba[index])),
                emergency=True,
            )

        ranked = self.model.predict_specializations(
            recognized, self.specialization_map, top_k=1
        )
        if not ranked:
            return None
        # summed probabilities can land a hair over 1.0 in floating point
        return Classification(
            specialization=ranked[0].specialization,
            confidence=min(1.0, ranked[0].probability),
        )


class SymptomExtractor:
    """Finds known symptom terms in a patient's sentence.

    The keyword matcher: used on its own without an OpenAI key, and as the
    backup when OpenAI extraction fails. Deliberately strict: exact terms,
    synonyms and long-word typos only. The model's own resolver also matches
    on word overlap, which would read a bare "pain" as stomach_pain.
    """

    def __init__(self, model: DiseaseModel):
        vocab = model.vocab
        self._known = {s: s for s in vocab.symptoms}
        for alias, target in vocab.synonyms.items():
            canonical = normalize(target)
            if canonical in vocab.index:
                self._known.setdefault(alias, canonical)
        self._squashed = {k.replace("_", ""): v for k, v in self._known.items()}
        self._single_words = {k: v for k, v in self._known.items() if "_" not in k}

    def __repr__(self) -> str:
        return "SymptomExtractor"

    def _lookup(self, key: str) -> str | None:
        if key in self._known:
            return self._known[key]
        return self._squashed.get(key.replace("_", ""))

    def _fuzzy(self, word: str) -> str | None:
        # short words are skipped: too many near-misses between unrelated terms
        if len(word) < _FUZZY_MIN_LENGTH:
            return None
        best, best_score = None, 0.0
        for candidate, target in self._single_words.items():
            score = SequenceMatcher(None, word, candidate).ratio()
            if score > best_score:
                best, best_score = target, score
        return best if best_score >= _FUZZY_CUTOFF else None

    def __call__(self, text: str) -> list[str]:
        # drop apostrophes so "can't" becomes "cant" and still matches
        cleaned = text.lower().replace("'", "").replace("’", "")
        found: list[str] = []
        for clause in _CLAUSE_BREAK.split(cleaned):
            for symptom in self._scan(_WORD.findall(clause)):
                if symptom not in found:
                    found.append(symptom)
        return found

    def _scan(self, words: list[str]) -> list[str]:
        found: list[str] = []
        i = 0
        while i < len(words):
            match, span = None, 1
            # longest phrase first, so "short of breath" wins over "breath"
            for n in range(min(_MAX_NGRAM, len(words) - i), 0, -1):
                match = self._lookup("_".join(words[i:i + n]))
                if match is not None:
                    span = n
                    break
            if match is None:
                match = self._fuzzy(words[i])

            # a denied symptom is worse than a missed one here: "not sweating,
            # no breathlessness" must not add up to a heart attack
            if match is not None and match not in found:
                if not _NEGATIONS & set(words[max(0, i - _NEGATION_WINDOW):i]):
                    found.append(match)
            i += span
        return found


def register_symptom_model() -> None:
    """Load the model and install it. ~1.5s and ~200MB, so call once at startup."""
    if not classifier_settings.enabled:
        logger.info("symptom model not loaded: CLASSIFIER_ENABLED is false")
        return

    model = DiseaseModel.load(MODEL_PATH)
    specialization_map = load_specialization_map(SPECIALIZATION_MAP_PATH)

    unknown = set(specialization_map.values()) - set(classifier.SPECIALIZATIONS)
    if unknown:
        logger.error("mapping uses departments the clinic lacks: %s", sorted(unknown))

    classifier.register(SymptomModelClassifier(model, specialization_map))

    keywords = SymptomExtractor(model)
    if openai_settings.extraction_configured:
        # keywords stay on as the backup for when OpenAI is slow or down
        classifier.register_extractor(
            OpenAISymptomExtractor(model.vocab.symptoms, fallback=keywords)
        )
        extraction = "OpenAI, keywords as backup"
    else:
        classifier.register_extractor(keywords)
        extraction = "keywords only"

    logger.info(
        "symptom model loaded: %s diseases, %s symptoms, extraction: %s",
        len(model.classes_),
        len(model.vocab),
        extraction,
    )
