"""
LLM fallback for messages the rule engine cannot answer (ENG-1659).

Where this sits in the pipeline:

    patient message
        -> predefined-responses/response.py  (rules, first match wins)
        -> if that returns None, this module
        -> if this also returns None, a safe canned reply

The rule engine stays in front for three reasons: it is free, it is instant,
and it is *predictable* — the emergency rule is guaranteed to fire before
anything reaches a model. Only genuinely unanticipated messages get here, which
also keeps the API bill proportional to how well rules.py is tuned. Every None
returned by the rule engine is both a fallback call and a signal that a keyword
is missing from rules.py.

Scope is deliberately narrow, per ENG-1659: general wellness guidance only, and
no diagnosis language. The system prompt enforces that, and it is the most
important part of this file — read it before changing anything here.

Failure policy: this function never raises. A clinic bot that 500s because
OpenAI is rate-limited is worse than one that says "let me connect you to
staff". Every error path logs and returns None.
"""

from __future__ import annotations

import logging

import openai
from openai import OpenAI

from chatbot.settings import openai_settings
from chatbot.predefined_responses import clinic

logger = logging.getLogger(__name__)

# Built once and reused. Constructing an OpenAI() per request rebuilds the
# underlying HTTP connection pool every time, which is pure added latency on a
# path where a patient is already waiting.
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=openai_settings.api_key,
            timeout=openai_settings.timeout_seconds,
            # The SDK retries connection errors and 429s on its own. Two is
            # enough here: a WhatsApp reply that takes 30s to arrive has
            # already failed as far as the patient is concerned.
            max_retries=2,
        )
    return _client


def _system_prompt() -> str:
    """The guardrails. This is the safety boundary, not decoration.

    Clinic facts are pulled from clinic.py at call time so the model is told the
    same address and hours the rule engine would give — and told not to invent
    the ones it wasn't given, which is the failure mode that actually hurts:
    a confidently wrong price or opening time sounds exactly like a right one.
    """
    return (
        f"You are the WhatsApp assistant for {clinic.NAME}. You are not a "
        "doctor and you never speak as one.\n\n"
        "ALLOWED: general, non-personalised wellness information — healthy "
        "eating, exercise, sleep, hydration, general guidance on managing "
        "diabetes or weight, and explaining what a medical term means.\n\n"
        "FORBIDDEN, without exception:\n"
        "- Do not diagnose. Never tell someone what condition they have or "
        "might have, even if they ask directly or describe clear symptoms.\n"
        "- Do not recommend, name, or dose any medication.\n"
        "- Do not interpret test results, scans, or lab values.\n"
        "- Do not tell anyone a symptom is harmless or that they need not "
        "come in.\n"
        "- Do not book, confirm, change, or cancel an appointment, and never "
        "state or imply that one is booked, held, or confirmed. A receptionist "
        "confirms every booking. You may take a preferred date and time, but "
        "say only that staff will confirm it.\n"
        "- Do not invent clinic details. If you were not given a fact below, "
        "say you will check with staff. Never guess a price, a doctor's name, "
        "an opening time, or an availability.\n\n"
        "For anything symptom-related, personal, or clinical, give at most one "
        "sentence of general context and then direct the patient to book an "
        "appointment or speak to staff.\n\n"
        "If the message suggests a medical emergency, tell them to call "
        f"{clinic.EMERGENCY_NUMBER} or go to the nearest emergency room "
        "immediately, and say nothing else.\n\n"
        "Facts you may state:\n"
        f"- Address: {clinic.ADDRESS}\n"
        f"- Open {clinic.OPENING_TIME} to {clinic.CLOSING_TIME}, "
        f"{clinic.OPEN_DAYS}\n"
        f"- Services: {clinic.SERVICES_SUMMARY}\n\n"
        "Style: this is WhatsApp. Two or three short sentences, plain language, "
        "no markdown, no bullet points, no emoji."
    )


def generate_fallback_reply(message: str) -> str | None:
    """Ask the model for a reply. Returns None if unavailable — never raises.

    None means "the caller should send its own safe canned reply", and covers
    both "not configured" and "the call failed". The caller should not care
    which.
    """
    if not message.strip():
        return None

    if not openai_settings.is_configured:
        # Debug, not warning: with a placeholder key this fires on every
        # unmatched message, and a warning per message would bury real errors.
        logger.debug("LLM fallback skipped: %s", openai_settings.explain())
        return None

    try:
        response = _get_client().chat.completions.create(
            model=openai_settings.model,
            max_completion_tokens=openai_settings.max_output_tokens,
            messages=[
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": message},
            ],
        )
    except openai.AuthenticationError:
        # Configuration error, not a transient one — surface it loudly, but
        # still without the key itself.
        logger.error(
            "OpenAI rejected the API key (%s). Check OPENAI_API_KEY in .env.",
            openai_settings.masked_key,
        )
        return None
    except openai.RateLimitError:
        logger.warning("OpenAI rate limit or quota exhausted; using canned reply.")
        return None
    except openai.APITimeoutError:
        logger.warning(
            "OpenAI timed out after %ss; using canned reply.",
            openai_settings.timeout_seconds,
        )
        return None
    except openai.APIConnectionError:
        logger.warning("Could not reach OpenAI; using canned reply.")
        return None
    except openai.APIStatusError as exc:
        logger.error("OpenAI returned %s: %s", exc.status_code, exc.message)
        return None
    except openai.OpenAIError:
        # Backstop for anything the SDK raises that is not covered above.
        # Broad on purpose — this function's contract is that it never raises.
        logger.exception("Unexpected OpenAI error; using canned reply.")
        return None

    if not response.choices:
        logger.warning("OpenAI returned no choices; using canned reply.")
        return None

    text = (response.choices[0].message.content or "").strip()
    return text or None
