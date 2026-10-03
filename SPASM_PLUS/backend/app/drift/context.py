"""
Context-drift dimension — replaces the previous `context = 1.0`
placeholder with real multi-turn contradiction detection (spec
section 6).

## What this actually does

Extracts simple negative "commitment" claims from prior assistant
turns — patterns like "I do not X", "I cannot X", "I will not X",
"I am not a Y" — within a configurable trailing window of the
conversation. Then checks whether the CURRENT response contains a
positive claim about the same predicate ("I do X", "I can X", "I
officially X", "I am a Y") with enough lexical overlap to plausibly
be the same claim being contradicted.

## Limitations (be honest)

This is regex + lexical-overlap pattern matching, NOT natural
language inference. It will:
- MISS most real contradictions that are phrased differently between
  turns (e.g. "I don't practice law" vs "as your representative in
  this matter" — no shared vocabulary, no match)
- Only catch contradictions where the same key verb/noun phrase
  recurs across turns (e.g. the "represent you in court" example
  from the spec works because "represent" appears in both turns)
- Occasionally false-positive on negation scope errors ("I don't
  think I should do X" vs "I will do X" might spuriously match)

This is a real, working first-pass implementation of the mechanism
the spec asks for, not a claim that it reliably detects contradiction
in general. A proper implementation would use an NLI model — flagged
as future work in RESEARCH.md.
"""
import re

_NEGATIVE_COMMITMENT_RE = re.compile(
    r"\bi (?:do not|don't|cannot|can't|will not|won't|am not|are not)\s+(?:an?\s+)?([a-z][a-z ]{2,40}?)(?:[.,!?]|$)",
    re.IGNORECASE,
)
_POSITIVE_CLAIM_RE = re.compile(
    r"\bi (?:do|can|will|am|officially|hereby)\s+(?:an?\s+)?([a-z][a-z ]{2,40}?)(?:[.,!?]|$)",
    re.IGNORECASE,
)

_STOPWORDS = {"a", "an", "the", "to", "you", "your", "this", "that", "it", "so", "just", "not"}


def _predicate_tokens(phrase: str) -> set[str]:
    return {w for w in re.findall(r"[a-z']+", phrase.lower()) if w not in _STOPWORDS and len(w) > 2}


def _extract_negative_commitments(text: str) -> list[str]:
    return [m.group(1).strip() for m in _NEGATIVE_COMMITMENT_RE.finditer(text)]


def _extract_positive_claims(text: str) -> list[str]:
    return [m.group(1).strip() for m in _POSITIVE_CLAIM_RE.finditer(text)]


def detect_context_drift(history: list[str], response_text: str, window: int = 10, overlap_threshold: float = 0.5) -> dict:
    """
    `history` is prior ASSISTANT message texts, oldest first. Only the
    last `window` are considered (spec: "support configurable
    conversation windows"). Returns {context_score, contradictions: [...]}.
    """
    if not history:
        return {"context_score": 1.0, "contradictions": []}

    windowed = history[-window:]
    commitments: list[str] = []
    for turn in windowed:
        commitments.extend(_extract_negative_commitments(turn))

    if not commitments:
        return {"context_score": 1.0, "contradictions": []}

    claims = _extract_positive_claims(response_text)
    contradictions = []
    for claim in claims:
        claim_tokens = _predicate_tokens(claim)
        if not claim_tokens:
            continue
        for commitment in commitments:
            commitment_tokens = _predicate_tokens(commitment)
            if not commitment_tokens:
                continue
            overlap = len(claim_tokens & commitment_tokens) / len(claim_tokens | commitment_tokens)
            if overlap >= overlap_threshold:
                contradictions.append(
                    {"prior_commitment": commitment, "contradicting_claim": claim, "overlap": round(overlap, 2)}
                )

    if not contradictions:
        return {"context_score": 1.0, "contradictions": []}

    # Each contradiction is a meaningful violation — penalize per contradiction, floor at 0.
    penalty = min(1.0, 0.5 * len(contradictions))
    return {"context_score": round(max(0.0, 1.0 - penalty), 2), "contradictions": contradictions}
