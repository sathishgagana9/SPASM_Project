"""
Identity-override guard — regex-based detector for "assume yourself
as X" / "pretend you are X" / "act as X" style persona-hijack phrasings.

## Role in the current architecture (changed from this module's first version)

This module is now used ONLY as the internal, degraded-mode fallback
inside `app.drift.intent_classifier.classify_intent()` — used when the
real semantic classifier call fails (Groq unreachable, malformed
output). It is NOT the primary defense anymore: the intent classifier
(an LLM call reasoning about the persona's actual configured scope)
replaced this as the primary gate, because a regex list can't do two
things the project's requirements call for: distinguish "explain what
a lawyer does" from "act as a lawyer", and catch plain topical
out-of-scope requests that never use a "become X" verb at all (e.g.
"can you explain this movie?" to a Teacher). See
`intent_classifier.py`'s module docstring for the full architecture.

This module is kept because a regex check is a reasonable fallback
when the classifier itself is unavailable — degraded but non-zero
defense is better than either failing open or failing fully closed on
every message during a transient Groq outage.
"""
import re

# Verb phrases that signal "become/act as someone or something else",
# not just "help me with X" — chosen to require a REASSIGNMENT framing,
# not merely the word "as" (which appears constantly in ordinary requests).
_REASSIGNMENT_PATTERNS = [
    r"\bassume\s+(yourself\s+as|the\s+(role|identity|persona)\s+of|you\s+are)\b",
    r"\bpretend\s+(to\s+be|you\s*'?re|you\s+are)\b",
    r"\bact\s+as\s+(if\s+you\s*'?re|if\s+you\s+are|a\s+different|another)\b",
    r"\byou\s+are\s+now\s+\w",
    r"\bfrom\s+now\s+on,?\s+you\s+are\b",
    r"\bbecome\s+(the\s+character|a\s+character|the\s+persona)\b",
    r"\broleplay\s+as\b",
    r"\bswitch\s+to\s+(being|the\s+persona\s+of|the\s+role\s+of)\b",
    r"\bignore\s+(your\s+|all\s+)?(previous|prior|earlier|current)\s+(instructions|persona|role|prompt)\b",
    r"\bforget\s+(you\s*'?re|you\s+are|your\s+(role|persona|identity))\b",
    r"\bact\s+as\s+the\s+\w",  # "act as the Joker" — narrower than bare "act as X" to reduce false positives
]

# If one of the patterns above matches BUT the sentence also contains one
# of these, treat it as a legitimate in-scope request rather than an
# identity reassignment (reduces false positives like "act as a sounding
# board for my essay" from a Teacher persona — still functioning AS the
# teacher, just being asked to take on a role WITHIN that identity).
_TARGET_EXCLUSIONS = [
    "sounding board", "devil's advocate", "study partner", "practice partner",
    "mock interviewer", "second pair of eyes", "proofreader",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _REASSIGNMENT_PATTERNS]


def detect_identity_override_attempt(user_message: str) -> tuple[bool, str | None]:
    """Returns (blocked, matched_pattern_description). Pure string matching,
    no LLM call — safe to run synchronously as classify_intent()'s fallback."""
    if not user_message:
        return False, None
    lower = user_message.lower()
    if any(exclusion in lower for exclusion in _TARGET_EXCLUSIONS):
        return False, None
    for pattern in _COMPILED_PATTERNS:
        match = pattern.search(user_message)
        if match:
            return True, f"User message matched identity-reassignment pattern: '{match.group(0)}'"
    return False, None
