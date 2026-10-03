"""
Deterministic rule checks: identity, behavior (forbidden phrases),
tone, instruction adherence, and knowledge-boundary
mention-vs-violation (spec section 7 — the "mentioning a boundary
vs violating it" fix).

All PROVISIONAL heuristics — see docs/drift-detection.md and
RESEARCH.md for the honesty caveats that apply project-wide.
"""
import re

_SLANG_MARKERS = ["lol", "lmao", "gonna", "wanna", "kinda", "yeah", "nah", "haha", "omg"]
_AI_DISCLAIMER_PATTERNS = [
    "i am an ai language model",
    "as an ai language model",
    "i'm just an ai",
    "as a large language model",
]
# Presence of any of these near a knowledge-boundary mention indicates the
# response is DECLINING/HEDGING rather than asserting — spec section 7.
_HEDGE_MARKERS = [
    "cannot", "can't", "unable to", "not able to", "do not", "don't",
    "won't", "will not", "should consult", "see a", "recommend seeing",
    "recommend consulting", "not a substitute", "general information",
    "not a diagnosis", "not legal advice", "outside my",
]


def _casualness_score(text: str) -> float:
    lower = text.lower()
    slang_hits = sum(lower.count(m) for m in _SLANG_MARKERS)
    exclamations = text.count("!")
    contractions = len(re.findall(r"\b\w+n't\b|\b\w+'re\b|\b\w+'ll\b|\b\w+'ve\b", lower))
    words = max(len(text.split()), 1)
    return (slang_hits * 2 + exclamations + contractions) / words


def check_identity(persona_identity: str, response_text: str) -> tuple[float, str | None]:
    if not persona_identity:
        return 1.0, None
    lower_resp = response_text.lower()
    if any(p in lower_resp for p in _AI_DISCLAIMER_PATTERNS):
        return 0.6, "Response used a generic AI disclaimer instead of staying in persona identity"
    return 1.0, None


def check_behavior(forbidden_behaviors: list[str], response_text: str) -> tuple[float, list[str]]:
    score = 1.0
    reasons = []
    for phrase in forbidden_behaviors:
        if phrase and phrase.lower() in response_text.lower():
            score = max(0.0, score - 0.5)
            reasons.append(f"Response matched a forbidden behavior: '{phrase}'")
    return score, reasons


def check_tone(persona_tone: str, response_text: str) -> tuple[float, str | None]:
    if persona_tone and any(k in persona_tone.lower() for k in ["formal", "academic", "professional"]):
        if _casualness_score(response_text) > 0.05:
            return 0.6, "Response tone reads casual/informal against a formal persona tone"
    return 1.0, None


def check_goals(goals: list[str], response_text: str) -> tuple[float, str | None]:
    if not goals:
        return 1.0, None
    lower_resp = response_text.lower()
    keywords = [w.lower() for g in goals for w in g.split() if len(w) > 4]
    if keywords and not any(k in lower_resp for k in keywords):
        return 0.8, "Response doesn't obviously reflect any configured persona goal (weak keyword check)"
    return 1.0, None


def check_knowledge_boundaries(boundaries: list[str], response_text: str) -> tuple[float, list[str]]:
    """
    Mention-vs-violation distinction: a boundary phrase appearing in a
    sentence alongside a hedge/refusal marker is treated as the persona
    correctly declining — not penalized. Only an ASSERTIVE mention
    (boundary phrase present, no hedge marker in that sentence) is
    penalized as a violation.
    """
    if not boundaries:
        return 1.0, []
    sentences = re.split(r"(?<=[.!?])\s+", response_text)
    score = 1.0
    reasons = []
    for boundary in boundaries:
        if not boundary:
            continue
        boundary_lower = boundary.lower()
        for sentence in sentences:
            if boundary_lower in sentence.lower():
                has_hedge = any(h in sentence.lower() for h in _HEDGE_MARKERS)
                if not has_hedge:
                    score = max(0.0, score - 0.5)
                    reasons.append(f"Response asserted about a knowledge boundary without hedging: '{boundary}'")
                break  # only evaluate the first matching sentence per boundary
    return score, reasons


def check_instruction(behavior_rules: list[str], response_text: str) -> tuple[float, list[str]]:
    score = 1.0
    reasons = []
    for rule in behavior_rules:
        if rule and f"not {rule.lower()}" in response_text.lower():
            score = max(0.0, score - 0.3)
            reasons.append(f"Response may contradict behavior rule: '{rule}'")
    return score, reasons
