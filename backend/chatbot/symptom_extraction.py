"""Reads symptoms out of a patient's own words with OpenAI.

The classifier only understands its own symptom names, such as "chest_pain".
OpenAI is made to answer with a list drawn from exactly those names, so "my
chest feels tight and I keep sweating" becomes ["chest_pain", "sweating"].

Any failure falls back to the keyword matcher, so this is never worse than
running without it.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Sequence

import openai

from chatbot.llm_fallback import get_client
from chatbot.settings import OpenAISettings, openai_settings

logger = logging.getLogger(__name__)

_PROMPT = (
    "You read one WhatsApp message from a clinic patient and list the symptoms "
    "they say they have now, using only the allowed names.\n"
    "- Leave out symptoms they say they do not have.\n"
    "- Match everyday, misspelled or Roman Urdu wording to the closest allowed "
    "name, but never add a symptom they did not describe.\n"
    "- If nothing matches, return an empty list.\n"
    "- Never diagnose."
)


class OpenAISymptomExtractor:
    def __init__(
        self,
        symptoms: Sequence[str],
        fallback: Callable[[str], Sequence[str]],
        client=None,
        settings: OpenAISettings = openai_settings,
    ):
        self._known = set(symptoms)
        self._fallback = fallback
        self._client = client  # tests pass a fake; otherwise the shared client
        self._settings = settings
        # the shape the answer must take. "enum" limits every item to a name
        # the classifier knows, so OpenAI cannot invent one
        self._response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "symptoms",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "symptoms": {
                            "type": "array",
                            "items": {"type": "string", "enum": sorted(self._known)},
                        },
                    },
                    "required": ["symptoms"],
                    "additionalProperties": False,
                },
            },
        }

    def __repr__(self) -> str:
        return "OpenAISymptomExtractor"

    def __call__(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        # log the kind of failure only: the message and its symptoms are
        # patient data
        try:
            return self._ask_openai(text)
        except openai.OpenAIError as exc:
            logger.warning(
                "OpenAI symptom extraction failed (%s), using keywords",
                type(exc).__name__,
            )
        except (ValueError, KeyError, TypeError, IndexError):
            logger.warning("OpenAI returned an unusable symptom list, using keywords")
        except Exception:
            logger.exception("OpenAI symptom extraction crashed, using keywords")
        return list(self._fallback(text))

    def _ask_openai(self, text: str) -> list[str]:
        client = self._client or get_client()
        response = client.chat.completions.create(
            model=self._settings.model,
            max_completion_tokens=self._settings.max_output_tokens,
            messages=[
                {"role": "system", "content": _PROMPT},
                {"role": "user", "content": text},
            ],
            response_format=self._response_format,
        )

        # content is None when the model refuses, and json.loads raises on it
        answer = json.loads(response.choices[0].message.content)
        names = answer["symptoms"]
        if not isinstance(names, list):
            raise TypeError("symptoms is not a list")

        found: list[str] = []
        for name in names:
            # strict mode already holds answers to the list; this checks again
            if name in self._known and name not in found:
                found.append(name)
        return found
