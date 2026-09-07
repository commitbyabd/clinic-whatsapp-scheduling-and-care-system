"""
Application configuration, loaded from the environment.

The rule this module exists to enforce: **secrets never live in source code.**
They arrive through the process environment. Locally that environment is
populated from a git-ignored .env file; in production the hosting platform
(Render, per ENG-1670) injects real environment variables and no .env file
exists at all. The code is identical in both cases — only the environment
differs, which is what makes the same artifact deployable anywhere.

Two consequences worth understanding:

  * `load_dotenv(override=False)` means a real environment variable always
    beats the .env file. Production is therefore unaffected by a stray .env,
    and you can override any single value for one run without editing a file:
    `OPENAI_MODEL=gpt-4o python -m uvicorn ...`

  * Nothing outside this module calls os.getenv() for a secret. One place
    reads configuration, one place validates it, and one place knows how to
    mask it for logging. Scattering os.getenv() through the codebase is how
    keys end up in log lines and error messages.

A missing or placeholder key is NOT a startup crash. This project's LLM call is
a *fallback* — the rule-based responder in predefined-responses/ answers most
messages on its own. Refusing to boot because an optional feature is
unconfigured would take the whole clinic bot offline over a nice-to-have. So
`OpenAISettings.is_configured` is False, the fallback is skipped, and the
service keeps answering. Config that a feature genuinely cannot run without
belongs in that feature's own startup check, not in a global assert here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# override=False: real environment variables win over the file. See module docs.
load_dotenv(_PROJECT_ROOT / ".env", override=False)


def _placeholder(value: str) -> bool:
    """True for the template values shipped in .env.example.

    Without this check a placeholder key reads as "configured", and the first
    sign of trouble is a 401 from OpenAI at runtime — on a real patient
    message. Catching it here turns a confusing production failure into a
    startup log line that says exactly what to fix.
    """
    return not value or "REPLACE_ME" in value.upper()


def _env_str(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _env_float(name: str, default: float) -> float:
    """Read a float, falling back to the default rather than crashing.

    A typo'd number in .env should not take the service down; the default is
    always a safe operating value.
    """
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
    """Everything needed to call OpenAI, plus whether we actually can.

    Frozen because configuration is read once at import and must not drift
    while the process runs — a mutable settings object that some request
    handler edits is a genuinely painful bug to track down.
    """

    api_key: str
    model: str
    timeout_seconds: float
    max_output_tokens: int
    enabled: bool

    @property
    def is_configured(self) -> bool:
        """Whether a real API call can be attempted.

        Checked before every fallback call. False means the key is absent or
        still the placeholder, or the fallback was switched off deliberately.
        """
        return self.enabled and not _placeholder(self.api_key)

    @property
    def masked_key(self) -> str:
        """The key in a form that is safe to log.

        Enough to confirm *which* key is loaded when debugging, never enough to
        use. Log this — never `api_key` itself. Anything written to a log is
        liable to end up in a monitoring service, a screenshot, or a ticket.
        """
        if _placeholder(self.api_key):
            return "<not configured>"
        if len(self.api_key) <= 10:
            return "<set>"
        return f"{self.api_key[:7]}...{self.api_key[-4:]}"

    def explain(self) -> str:
        """One line describing config state, for a startup log."""
        if not self.enabled:
            return "LLM fallback: disabled via LLM_FALLBACK_ENABLED"
        if _placeholder(self.api_key):
            return (
                "LLM fallback: INACTIVE — OPENAI_API_KEY is unset or still the "
                "placeholder. Rule-based responses only. Set a real key in .env "
                "to enable it."
            )
        return (
            f"LLM fallback: active — model={self.model} "
            f"key={self.masked_key} timeout={self.timeout_seconds}s"
        )


openai_settings = OpenAISettings(
    api_key=_env_str("OPENAI_API_KEY", ""),
    model=_env_str("OPENAI_MODEL", "gpt-4o-mini"),
    timeout_seconds=_env_float("OPENAI_TIMEOUT_SECONDS", 10.0),
    max_output_tokens=_env_int("OPENAI_MAX_OUTPUT_TOKENS", 300),
    enabled=_env_bool("LLM_FALLBACK_ENABLED", True),
)


@dataclass(frozen=True)
class ClassifierSettings:
    """Settings for the outsourced ML symptom classifier (ENG-1660).

    No key or endpoint here yet: the model is expected in-process, registered
    at startup. If it ships as an HTTP service instead, a base URL and timeout
    belong here — not scattered through classifier.py.
    """

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
    # Deliberately conservative. A wrong department wastes a patient's trip and
    # a receptionist's time, so an unsure prediction is better handed to the
    # LLM fallback, which will simply ask them to book. Tune once the delivered
    # model's real precision/recall numbers are known — not before.
    min_confidence=_env_float("CLASSIFIER_MIN_CONFIDENCE", 0.6),
)


@dataclass(frozen=True)
class TwilioSettings:
    """Settings for the WhatsApp webhook (ENG-1653).

    Unlike the two above, this one is NOT fail-soft. The others guard optional
    features, so an unconfigured key just disables them. This guards a security
    control: without the auth token the endpoint cannot tell a real Twilio
    request from anybody who found the URL. An unconfigured webhook therefore
    refuses requests rather than accepting them — see `skip_signature_check`.
    """

    auth_token: str
    # Escape hatch for local curl testing before the token arrives. Must be set
    # deliberately; it is never the default, so a deploy that forgets the token
    # fails closed instead of silently serving an open endpoint.
    skip_signature_check: bool
    # Twilio signs the exact public URL it called. Behind ngrok or Render the
    # app sees an internal URL instead, and the signatures will not match. Set
    # this to the full public webhook URL when that happens; leave it empty to
    # reconstruct from the request's forwarded headers.
    webhook_url: str

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
                "Twilio webhook: INACTIVE — TWILIO_AUTH_TOKEN is unset or still "
                "the placeholder, so requests cannot be verified and will be "
                "refused. Set the token from the Twilio console."
            )
        return "Twilio webhook: active, signature checking on"


twilio_settings = TwilioSettings(
    auth_token=_env_str("TWILIO_AUTH_TOKEN", ""),
    skip_signature_check=_env_bool("TWILIO_SKIP_SIGNATURE_CHECK", False),
    webhook_url=_env_str("TWILIO_WEBHOOK_URL", ""),
)
