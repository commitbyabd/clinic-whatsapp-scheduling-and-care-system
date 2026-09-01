"""
Rule-based responses for common patient queries (ENG-1658).

The underscore in the package name is load-bearing: a hyphen would make this
directory un-importable, forcing every caller to manipulate sys.path instead.

Layout:
    clinic.py    per-deployment facts (address, hours, phone)
    rules.py     the intent table — what patients type, what we say back
    response.py  the matcher — decides which rule a message hits

Import the matcher, not the internals:

    from predefined_responses.response import match_rule, match_response
"""

from chatbot.predefined_responses.response import match_response, match_rule

__all__ = ["match_response", "match_rule"]
