"""OpenAI fallback for messages the rule engine could not answer (ENG-1659).

Only reached when rules miss, so the bill is proportional to how well rules.py
is tuned. Never raises; every failure path returns None and the caller sends a
canned reply.
"""

from __future__ import annotations

import logging

import openai
from openai import OpenAI

from chatbot.settings import openai_settings
from chatbot.predefined_responses import clinic

logger = logging.getLogger(__name__)

# built once. A new client per request rebuilds the connection pool, which is
# pure added latency on a path where a patient is waiting.
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=openai_settings.api_key,
            timeout=openai_settings.timeout_seconds,
            max_retries=2,
        )
    return _client


def _system_prompt() -> str:
    """The guardrails. This is the safety boundary, not decoration."""
    # clinic facts are injected so the model states the same address and hours
    # the rule engine would, and is told not to invent the ones it lacks
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
    """Ask the model for a reply, or None if unavailable. Never raises."""
    if not message.strip():
        return None

    if not openai_settings.is_configured:
        # debug, not warning: with a placeholder key this fires on every
        # unmatched message and would bury real errors
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
        # configuration error rather than a transient one, so log it loudly
        logger.error(
            "OpenAI rejected the API key (%s). Check OPENAI_API_KEY.",
            openai_settings.masked_key,
        )
        return None
    except openai.RateLimitError:
        logger.warning("OpenAI rate limit or quota exhausted, using canned reply")
        return None
    except openai.APITimeoutError:
        logger.warning(
            "OpenAI timed out after %ss, using canned reply",
            openai_settings.timeout_seconds,
        )
        return None
    except openai.APIConnectionError:
        logger.warning("Could not reach OpenAI, using canned reply")
        return None
    except openai.APIStatusError as exc:
        logger.error("OpenAI returned %s: %s", exc.status_code, exc.message)
        return None
    except openai.OpenAIError:
        # backstop, so this function's never-raises contract holds
        logger.exception("Unexpected OpenAI error, using canned reply")
        return None

    if not response.choices:
        logger.warning("OpenAI returned no choices, using canned reply")
        return None

    text = (response.choices[0].message.content or "").strip()
    return text or None
