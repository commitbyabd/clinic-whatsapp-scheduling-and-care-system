"""Seam for the outsourced ML symptom classifier (ENG-1660).

Pipeline, note the OpenAI step comes BEFORE this and is a different call from
the wellness fallback in llm_fallback.py:

    patient free text -> OpenAI extraction -> ["chest_pain", ...] -> this model

Contract the delivered model must satisfy:

    def predict(symptoms: list[str]) -> Classification | None

    symptoms        extracted terms, roughly aligned to the Kaggle 132-symptom
                    vocabulary but not guaranteed to match it exactly, since
                    the extraction step is an LLM. Match fuzzily.
    returns         None when the symptoms do not support one confident
                    specialization. A valid answer, not a failure.
    specialization  one of SPECIALIZATIONS below. Never a disease name.
    confidence      0.0-1.0, honest.

    Must not raise. Should be fast, a patient is waiting.

If the model does not match this signature, write an adapter and register that
rather than changing the contract, so a v2 model cannot ripple through the code.

    classifier.register(lambda symptoms: adapt(their_predict(symptoms)))
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Sequence

from chatbot.settings import classifier_settings

logger = logging.getLogger(__name__)

SPECIALIZATIONS = (
    "General Physician",
    "Dermatologist",
    "Pulmonologist",
    "Neurologist",
    "Orthopedist",
    "ENT Specialist",
    "Gynecologist",
    "Pediatrician",
    "General Surgeon",
    "Urologist",
    "Cardiologist",
    "Endocrinologist",
)

# an unsure model should widen the net, not narrow it
DEFAULT_SPECIALIZATION = "General Physician"


@dataclass(frozen=True)
class Classification:
    specialization: str
    confidence: float

    def is_valid(self) -> bool:
        # rejects a disease name, a department the clinic does not have, and
        # confidence given as a percentage
        return (
            self.specialization in SPECIALIZATIONS
            and isinstance(self.confidence, (int, float))
            and not isinstance(self.confidence, bool)
            and 0.0 <= float(self.confidence) <= 1.0
        )


SymptomClassifier = Callable[[Sequence[str]], "Classification | None"]

_classifier: SymptomClassifier | None = None


def register(fn: SymptomClassifier) -> None:
    """Install the classifier. Call once at startup."""
    global _classifier
    _classifier = fn
    logger.info("symptom classifier registered: %s", getattr(fn, "__name__", fn))


def is_registered() -> bool:
    return _classifier is not None


def classify(symptoms: Sequence[str]) -> Classification | None:
    """Predict a specialization, or None if unavailable. Never raises.

    None covers not-registered, disabled, empty input, low-confidence,
    malformed and crashed alike; the caller does not need to know which.
    """
    if not classifier_settings.enabled or _classifier is None:
        return None

    cleaned = [s.strip() for s in symptoms or () if s and s.strip()]
    if not cleaned:
        return None

    try:
        result = _classifier(cleaned)
    except Exception:
        # broad on purpose: an outsourced model must not take the bot down
        logger.exception("symptom classifier raised, falling back")
        return None

    if result is None:
        return None

    if not isinstance(result, Classification) or not result.is_valid():
        logger.warning("classifier returned malformed output, ignoring: %r", result)
        return None

    if result.confidence < classifier_settings.min_confidence:
        # symptoms are health data, so log the score and not the terms
        logger.info(
            "classification below threshold (%.2f < %.2f)",
            result.confidence,
            classifier_settings.min_confidence,
        )
        return None

    return result
