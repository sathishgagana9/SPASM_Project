"""
Drift Detection Engine — v2 (research-grade hybrid detector).

Formally: D_t = f(P, U_t, R_t, H_t) — persona, user request, response,
and conversation history all feed the decision (spec section 4).
This replaces the v1 detector's response-only analysis, which could
not distinguish "answered an out-of-scope question" from "correctly
refused an out-of-scope question" (both mentioned the same words).

## Architecture

- rules.py     deterministic checks: identity, behavior, tone, goals,
                instruction, and boundary mention-vs-violation
- scope.py     scope-adherence: in-scope / appropriate_refusal /
                out_of_scope_violation / over_refusal / borderline
- context.py   multi-turn contradiction detection (replaces the old
                fixed context=1.0 placeholder)
- semantic.py  lexical-cosine similarity by default; optional real
                embedding backend if configured
- scoring.py   formal weighted stability score, severity thresholds,
                decoupled drift_score / drift_probability / confidence

## Still true from v1, unchanged

This is a heuristic system, not a trained classifier or validated
statistical model. Every score is a deterministic function of real
inputs — nothing here is fabricated or randomized — but none of the
scoring logic has been validated against labeled drift data. See
RESEARCH.md and docs/drift-detection.md for the full honesty
statement, and research/evaluation/ for how to actually validate
this against SPASM-DriftBench once you're ready to run that.

Backward compatible: `detect_drift(persona, response_text)` still
works exactly as before (existing call sites, existing tests) —
`user_prompt` and `history` are optional and unlock the new scope
and context dimensions when provided.
"""
from app.drift import rules
from app.drift.context import detect_context_drift
from app.drift.conformal import conformal_drift_test
from app.drift.multivariate_conformal import attributable_conformal_drift
from app.drift.sequential_conformal import SequentialConformalState
from app.drift.scope import classify_scope
from app.drift.scoring import (
    DETECTOR_VERSION,
    THRESHOLD_VERSION,
    classify_severity,
    compute_confidence,
    compute_drift_probability,
    compute_stability,
)
from app.models.persona import Persona


def detect_drift(
    persona: Persona,
    response_text: str,
    user_prompt: str = "",
    history: list[str] | None = None,
    weights: dict[str, float] | None = None,
    context_window: int = 10,
    conformal_calibration_texts: list[str] | None = None,
    sequential_state: SequentialConformalState | None = None,
    dimension_calibration_texts: dict[str, list[str]] | None = None,
    fdr_q: float = 0.05,
) -> dict:
    """
    `history` is prior ASSISTANT message texts (oldest first), used
    for the context dimension only. `user_prompt` is the message that
    triggered `response_text`, used for the scope dimension only.
    Both are optional — omitting them just means those two dimensions
    default to "not evaluated" (score 1.0, not penalized), same as v1
    behavior for `context`.
    """
    scores: dict[str, float] = {}
    reasons: list[str] = []
    extra: dict = {}

    scores["identity"], identity_reason = rules.check_identity(persona.identity, response_text)
    if identity_reason:
        reasons.append(identity_reason)

    scope_result = classify_scope(persona.scope, user_prompt, response_text)
    scores["scope"] = scope_result["scope_score"]
    extra["scope_classification"] = scope_result["classification"]
    extra["scope_similarity"] = scope_result["topical_similarity"]
    extra["scope_similarity_backend"] = scope_result["similarity_backend"]
    if scope_result["classification"] == "out_of_scope_violation":
        reasons.append(
            f"Response answered a request outside persona scope instead of declining "
            f"(topical similarity to scope: {scope_result['topical_similarity']})"
        )
    elif scope_result["classification"] == "over_refusal":
        reasons.append("Response declined a request that appears to be within persona scope (possible over-refusal)")
    elif scope_result["classification"] == "low_signal_not_flagged":
        extra["scope_note"] = (
            "Low lexical similarity to persona scope, but not confidently flagged as a violation — "
            "see backend/app/drift/scope.py docstring for why this is deliberately conservative."
        )

    behavior_score, behavior_reasons = rules.check_behavior(persona.forbidden_behaviors, response_text)
    scores["behavior"] = behavior_score
    reasons.extend(behavior_reasons)

    tone_score, tone_reason = rules.check_tone(persona.tone, response_text)
    scores["tone"] = tone_score
    if tone_reason:
        reasons.append(tone_reason)

    goals_score, goals_reason = rules.check_goals(persona.goals, response_text)
    scores["goals"] = goals_score
    if goals_reason:
        reasons.append(goals_reason)

    knowledge_score, knowledge_reasons = rules.check_knowledge_boundaries(persona.knowledge_boundaries, response_text)
    scores["knowledge"] = knowledge_score
    reasons.extend(knowledge_reasons)

    instruction_score, instruction_reasons = rules.check_instruction(persona.behavior_rules, response_text)
    scores["instruction"] = instruction_score
    reasons.extend(instruction_reasons)

    context_result = detect_context_drift(history or [], response_text, window=context_window)
    scores["context"] = context_result["context_score"]
    extra["context_contradictions"] = context_result["contradictions"]
    if context_result["contradictions"]:
        reasons.append(
            f"Response contradicts {len(context_result['contradictions'])} earlier commitment(s) in this conversation"
        )

    overall = compute_stability(scores, weights)
    drift_score = round(1.0 - overall, 4)
    severity = classify_severity(overall)
    detected = severity != "low"

    lowest_dim = min(scores, key=lambda d: scores[d])
    drift_type = f"{lowest_dim}_drift" if detected else "none"

    # Optional research-grade statistical layers. They are opt-in so the
    # legacy detector remains backward compatible, while experiments can run
    # the full SPASM++ loop without duplicating feature extraction.
    if conformal_calibration_texts is not None:
        conformal_result = conformal_drift_test(response_text, conformal_calibration_texts)
        if conformal_result is None:
            extra["conformal"] = {"status": "insufficient_calibration"}
        else:
            conformal_payload = {
                "status": "evaluated",
                "p_value": conformal_result.p_value,
                "nonconformity_score": conformal_result.nonconformity_score,
                "n_calibration": conformal_result.n_calibration,
                "backend": conformal_result.backend,
            }
            if sequential_state is not None:
                conformal_payload["sequential"] = sequential_state.update(conformal_result.p_value)
            extra["conformal"] = conformal_payload

    if dimension_calibration_texts is not None:
        extra["attributable_conformal"] = attributable_conformal_drift(
            response_text, dimension_calibration_texts, fdr_q=fdr_q
        )

    return {
        "detected": detected,
        "drift_type": drift_type,
        "severity": severity if detected else "low",
        "confidence": compute_confidence(overall),
        "drift_probability": compute_drift_probability(drift_score),
        "dimensions": {k: round(v, 2) for k, v in scores.items()},
        "overall_stability": round(overall, 2),
        "reason": "; ".join(reasons) if reasons else "No rule violations detected",
        "method": "rule_based",
        "detector_version": DETECTOR_VERSION,
        "threshold_version": THRESHOLD_VERSION,
        **extra,
    }
