"""Decides which rule a message hits. The table itself lives in rules.py.

Three passes, first match wins: emergency, then messages that are only a
greeting or thank-you, then the rules.py table top to bottom. Text is
lower-cased and punctuation flattened first, and keywords match on word
boundaries so "hi" cannot match inside "which".
"""

import re

from chatbot.predefined_responses.rules import (
    FAREWELL_KEYWORDS,
    FAREWELL_RESPONSE,
    GREETING_KEYWORDS,
    GREETING_RESPONSE,
    RAW_RULES,
    RawRule,
)


class Rule(RawRule):
    """A rule from rules.py with its compiled matcher attached."""

    pattern: re.Pattern[str]


# Keep apostrophes and hyphens: they are part of real keywords ("can't
# breathe", "check-up"). Everything else — punctuation, emoji, symbols —
# becomes a space so it can act as a word boundary.
_PUNCTUATION = re.compile(r"[^\w\s'-]+")
_WHITESPACE = re.compile(r"\s+")

# Trailing words we still treat as part of a bare greeting/farewell, so
# "thanks a lot" and "hello doctor" are handled as small talk in pass 2.
_STANDALONE_FILLER = (
    r"(?:\s+(?:a lot|so much|very much|so much for your help|there|again|"
    r"sir|madam|doc|doctor|team|everyone|all))?"
)


def _normalize(message: str) -> str:
    """Lower-case, flatten punctuation/emoji to spaces, collapse whitespace."""
    text = _PUNCTUATION.sub(" ", message.lower())
    return _WHITESPACE.sub(" ", text).strip()


def _compile(keywords: list[str], *, whole_message: bool = False) -> re.Pattern[str]:
    """Compile keywords into a single regex.

    Word boundaries stop 'hi' matching inside 'which'. Keywords are sorted
    longest-first so the alternation prefers the most specific match.
    IGNORECASE is belt-and-braces: input is already lower-cased, but this
    keeps a capitalised keyword in rules.py from silently becoming dead code.

    With whole_message=True the pattern only matches when the message consists
    of nothing but that keyword (plus optional filler).
    """
    if not keywords:
        raise ValueError("a rule needs at least one keyword")
    body = "|".join(re.escape(kw) for kw in sorted(keywords, key=len, reverse=True))
    if whole_message:
        return re.compile(rf"\A(?:{body}){_STANDALONE_FILLER}\Z", re.IGNORECASE)
    return re.compile(rf"\b(?:{body})\b", re.IGNORECASE)


RULES: dict[str, Rule] = {
    name: {**rule, "pattern": _compile(rule["keywords"])}
    for name, rule in RAW_RULES.items()
}

# Pass 2: the same greeting/farewell responses, but only when the message is
# nothing else. These cannot collide with the emergency keywords, so running
# them straight after the emergency rule is safe.
_STANDALONE_RULES: dict[str, Rule] = {
    "greeting": {
        "keywords": GREETING_KEYWORDS,
        "response": GREETING_RESPONSE,
        "pattern": _compile(GREETING_KEYWORDS, whole_message=True),
    },
    "farewell": {
        "keywords": FAREWELL_KEYWORDS,
        "response": FAREWELL_RESPONSE,
        "pattern": _compile(FAREWELL_KEYWORDS, whole_message=True),
    },
}

# The full evaluation order, flattened once at import time.
_MATCH_ORDER: list[tuple[str, Rule]] = [
    ("emergency", RULES["emergency"]),
    *_STANDALONE_RULES.items(),
    *((name, rule) for name, rule in RULES.items() if name != "emergency"),
]


def match_rule(message: str) -> tuple[str, str] | None:
    """Return (rule_name, response) for the first matching rule, or None.

    The rule name is useful for logging and analytics — the messages that
    return None are the ones telling you which keywords to add to rules.py
    next. Use match_response() when you only need the text to send back.
    """
    text = _normalize(message)
    if not text:
        return None
    for name, rule in _MATCH_ORDER:
        if rule["pattern"].search(text):
            return name, rule["response"]
    return None


def match_response(message: str) -> str | None:
    match = match_rule(message)
    return match[1] if match is not None else None


def is_emergency(message: str) -> bool:
    """Whether the message trips the emergency rule, checked on its own.

    Exposed separately from match_rule() because the scripted question flow
    must never be able to swallow an emergency. A patient halfway through
    booking who types "chest pain" is answering a menu as far as the flow is
    concerned; this lets the orchestrator check for an emergency *before* the
    reply is interpreted as a menu selection.
    """
    text = _normalize(message)
    return bool(text) and bool(RULES["emergency"]["pattern"].search(text))


EMERGENCY_RESPONSE = RULES["emergency"]["response"]
