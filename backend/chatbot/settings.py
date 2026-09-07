"""Chatbot configuration, read from the environment.

Secrets never live in source. Locally they come from a git-ignored .env; in
production the platform sets real environment variables and no .env exists.
Nothing outside this module reads a secret, so there is one place that knows
how to mask one for logging.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# override=False so a real environment variable always beats the file
load_dotenv(_PROJECT_ROOT / ".env", override=False)


def _placeholder(value: str) -> bool:
    # without this a placeholder key reads as configured, and the first sign of
    # trouble is a 401 on a live patient message
    return not value or "REPLACE_ME" in value.upper()


def _env_str(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _env_float(name: str, default: float) -> float:
    # a typo in .env should not take the service down
    try:
        return float(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class OpenAISettings:
    api_key: str
    model: str
    timeout_seconds: float
    max_output_tokens: int
    enabled: bool

    @property
    def is_configured(self) -> bool:
        return self.enabled and not _placeholder(self.api_key)

    @property
    def masked_key(self) -> str:
        """Safe to log. Never log api_key itself."""
        if _placeholder(self.api_key):
            return "<not configured>"
        if len(self.api_key) <= 10:
            return "<set>"
        return f"{self.api_key[:7]}...{self.api_key[-4:]}"

    def explain(self) -> str:
        if not self.enabled:
            return "LLM fallback: disabled via LLM_FALLBACK_ENABLED"
        if _placeholder(self.api_key):
            return (
                "LLM fallback: INACTIVE — OPENAI_API_KEY is unset or still the "
                "placeholder. Rule-based responses only."
            )
        return (
            f"LLM fallback: active — model={self.model} "
            f"key={self.masked_key} timeout={self.timeout_seconds}s"
        )


# a missing key disables the fallback rather than stopping startup; the rule
# engine answers most messages on its own
openai_settings = OpenAISettings(
    api_key=_env_str("OPENAI_API_KEY", ""),
    model=_env_str("OPENAI_MODEL", "gpt-4o-mini"),
    timeout_seconds=_env_float("OPENAI_TIMEOUT_SECONDS", 10.0),
    max_output_tokens=_env_int("OPENAI_MAX_OUTPUT_TOKENS", 300),
    enabled=_env_bool("LLM_FALLBACK_ENABLED", True),
)


@dataclass(frozen=True)
class ClassifierSettings:
    enabled: bool
    min_confidence: float

    def explain(self) -> str:
        if not self.enabled:
            return "Symptom classifier: disabled via CLASSIFIER_ENABLED"
        return (
            "Symptom classifier: enabled, discarding predictions below "
            f"{self.min_confidence:.2f} confidence (inactive until a model is "
            "registered)"
        )


classifier_settings = ClassifierSettings(
    enabled=_env_bool("CLASSIFIER_ENABLED", True),
    # conservative: a wrong department wastes a patient's trip, so an unsure
    # prediction is better handed to the LLM. Tune once the real model's
    # precision and recall are known.
    min_confidence=_env_float("CLASSIFIER_MIN_CONFIDENCE", 0.6),
)


@dataclass(frozen=True)
class TwilioSettings:
    """Unlike the two above, this one is not fail-soft.

    Those guard optional features. This guards a security control, so an
    unconfigured webhook refuses requests rather than serving an open endpoint.
    """

    auth_token: str
    skip_signature_check: bool
    webhook_url: str  # set only if signatures fail behind a proxy

    @property
    def is_configured(self) -> bool:
        return bool(self.auth_token) and not _placeholder(self.auth_token)

    def explain(self) -> str:
        if self.skip_signature_check:
            return (
                "Twilio webhook: SIGNATURE CHECKING DISABLED — local testing "
                "only. Never run this way anywhere reachable from the internet."
            )
        if not self.is_configured:
            return (
                "Twilio webhook: INACTIVE — TWILIO_AUTH_TOKEN is unset, so "
                "requests cannot be verified and will be refused."
            )
        return "Twilio webhook: active, signature checking on"


twilio_settings = TwilioSettings(
    auth_token=_env_str("TWILIO_AUTH_TOKEN", ""),
    # defaults to False so a deploy that forgets the token fails closed
    skip_signature_check=_env_bool("TWILIO_SKIP_SIGNATURE_CHECK", False),
    webhook_url=_env_str("TWILIO_WEBHOOK_URL", ""),
)
