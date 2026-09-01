"""
Seam for the outsourced ML symptom classifier (ENG-1660, Phase 2).

The model is built elsewhere. This module is the boundary it plugs into, so the
rest of the system can be finished and demoed before the model exists, and so
nothing about the model's internals leaks into the orchestrator.

Today `classify()` returns None and the system behaves as if this layer were
absent. When the model arrives, one adapter is registered at startup.


WHERE THIS SITS — note the OpenAI step BEFORE it, not after
-----------------------------------------------------------
    patient describes symptoms in free text, inside the scripted question flow
        -> OpenAI extraction  ->  ["chest_pain", "breathlessness", ...]
        -> THIS MODEL         ->  "Cardiologist"
        -> route the appointment request to that specialization

This is the opposite order from the general wellness fallback in
llm_fallback.py, which is a *different* OpenAI call for a different purpose.
Do not confuse the two: extraction turns prose into symptom terms; the fallback
answers general questions. Only extraction feeds this model.

Consequence for the input type: this model does NOT receive raw WhatsApp text.
It receives already-extracted symptom terms. An earlier version of this file had
that backwards.


CONTRACT FOR THE OUTSOURCED MODEL
---------------------------------
Deliver anything you like internally — sklearn pipeline, pickle, ONNX, a local
HTTP service. We require exactly one callable:

    def predict(symptoms: list[str]) -> Classification | None

  symptoms        extracted symptom terms, already cleaned by the OpenAI step.
                  Roughly aligned to the Kaggle 132-symptom vocabulary, but
                  NOT guaranteed to match it exactly — the extraction step is
                  an LLM and is not deterministic. Expect synonyms
                  ("shortness of breath" vs "breathlessness"), spacing and
                  underscore variation, and occasional terms outside the
                  vocabulary. Match fuzzily; do not require exact strings.
                  May be empty — return None if so.

  returns         a Classification, or None when the symptoms do not support a
                  confident single specialization. None is a valid answer, not
                  a failure — it routes the patient to General Physician via
                  the normal booking flow rather than guessing a department.

  specialization  exactly one of SPECIALIZATIONS below. Anything else is
                  logged and discarded — a patient must never be sent to a
                  department the clinic does not have.
  confidence      0.0-1.0, honest. Below CLASSIFIER_MIN_CONFIDENCE is
                  discarded, which is the right outcome for a guess.

  must not raise  wrap your own errors and return None.
  should be fast  a patient is waiting on a WhatsApp reply.

If the delivered model does not match this signature, write an adapter that
converts its output into a Classification and register *that*. Do not change
this contract to fit the model — the adapter is where the mismatch belongs, so
a v2 model cannot ripple through the codebase.

Note: the model is trained on 41 diseases mapped down to these 12
specializations, but it must return the SPECIALIZATION, never the disease. The
disease name must not reach a patient — naming a condition is a diagnosis, and
this system does not make them.


WIRING IT UP
------------
At startup, once the model exists:

    import classifier
    from their_package import predict as their_predict

    classifier.register(lambda symptoms: adapt(their_predict(symptoms)))

`register()` is a runtime call, not an import, so a missing or broken model
package can never stop the service from booting.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Sequence

from chatbot.settings import classifier_settings

logger = logging.getLogger(__name__)

# The clinic's 12 departments. The model may return nothing else.
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

# Where an unusable prediction lands. Chosen because a General Physician can
# triage anything — an unsure model should widen the net, never narrow it.
DEFAULT_SPECIALIZATION = "General Physician"


@dataclass(frozen=True)
class Classification:
    specialization: str
    confidence: float

    def is_valid(self) -> bool:
        """Reject malformed output rather than trusting an external model.

        A model returning a disease name, a department the clinic lacks, or
        `confidence=87` (percent, not a fraction) must degrade to the normal
        booking flow — not crash the service and not send a patient to a
        department that does not exist.
        """
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
    """Predict a specialization. Returns None when unavailable — never raises.

    None means "the caller should fall back to the normal booking flow", and
    covers not-registered, disabled, empty input, low-confidence, malformed,
    and crashed alike. The caller does not need to know which.
    """
    if not classifier_settings.enabled or _classifier is None:
        return None

    cleaned = [s.strip() for s in symptoms or () if s and s.strip()]
    if not cleaned:
        return None

    try:
        result = _classifier(cleaned)
    except Exception:
        # Broad by design: an outsourced model must never take the clinic bot
        # down. Logged with a traceback so the failure stays visible.
        logger.exception("symptom classifier raised; falling back to booking flow")
        return None

    if result is None:
        return None

    if not isinstance(result, Classification) or not result.is_valid():
        logger.warning("classifier returned malformed output, ignoring: %r", result)
        return None

    if result.confidence < classifier_settings.min_confidence:
        logger.info(
            "classification below threshold (%.2f < %.2f) for %r",
            result.confidence,
            classifier_settings.min_confidence,
            cleaned,
        )
        return None

    return result
