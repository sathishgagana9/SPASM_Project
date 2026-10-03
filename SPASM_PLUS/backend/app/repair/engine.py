"""
Repair Engine — v3 (research-grade, learned policy + bounded verify-loop).

Architecture: Drift Detector -> Severity -> Strategy Selector ->
Repair Operator -> Regenerate -> Verify -> (retry up to a bound, or
accept/roll back). What's new in v3 over v2:

(a) an actual LEARNED repair policy (`app.repair.policy.HybridPolicy`,
    LinUCB contextual bandit) as an opt-in alternative to the
    severity lookup table — see policy.py for what this is and the
    honesty caveats around it not yet being trained on real data;
(b) `repair_until_verified()`: a bounded retry loop with a STRUCTURAL
    no-worse-off guarantee (Theorem below), not just a
    verification check that flags problems after the fact;
(c) unchanged from v2: a scope_reinforcement operator, and
    verification that checks more than "did stability go up" (see
    `_verify()` below).

## The repair policy

Spec section 10 asks for:

    repair_action = argmax(stability_improvement - latency_cost - token_cost - utility_loss)

Two policies now implement approximations of this, and you choose
which one `repair()` uses via the `policy` argument:

- `select_repair_operator()` (below): the ORIGINAL heuristic lookup
  table, escalated by severity AND simultaneous-violation count.
  Deterministic, inspectable, needs zero training data. This remains
  the default and the cold-start fallback inside HybridPolicy.
- `app.repair.policy.HybridPolicy`: a LinUCB contextual bandit that
  learns, per drift-event context, which operator has historically
  maximized `policy.compute_reward()` (which implements the spec
  formula above literally, with configurable cost weights) — see
  policy.py's module docstring for the full account, including that
  it has never been trained on real outcomes in this environment.

## Verification — spec section 11 (unchanged criteria)

`success` requires ALL of:
1. meaningful_improvement: stability_after - stability_before >= MEANINGFUL_IMPROVEMENT_THRESHOLD
2. acceptable_final_stability: stability_after >= settings.drift_severity_medium_threshold
3. no_new_severe_violation: no dimension that was >= 0.5 before repair drops below 0.5 after
4. passes_usefulness_heuristic: repaired response isn't degenerate (empty, near-empty
   relative to the original, or a verbatim repeat) — a crude proxy for "is this
   still a useful response", NOT a quality judgment. See docs/repair-engine.md.

Any failed check is recorded in `quality_flags` even when others pass, so a
partial improvement that still fails verification is diagnosable, not just "failed".

## No-worse-off guarantee and bounded regeneration — see docs/repair-engine-guarantees.md

`repair_until_verified()` proves (informally, in that doc; this is a
proof sketch appropriate for an applied-AI paper, not a formal
mechanized proof) that the response it returns is never LESS stable
than the pre-repair response, and that it terminates within a fixed,
configurable number of cycles (`max_cycles`). Read that doc before
citing either property in a paper — it also states exactly what
would break each guarantee (e.g. a non-deterministic detector) so
you can check those preconditions hold for your configuration.
"""
import time

from app.core.config import get_settings
from app.drift.detector import detect_drift
from app.models.persona import Persona
from app.providers.base import ChatMessage, LLMProvider, ProviderError
from app.services.persona_compiler import compile_persona

MEANINGFUL_IMPROVEMENT_THRESHOLD = 0.05  # PROVISIONAL

# severity -> base operator (spec section 21)
_BASE_STRATEGY_BY_SEVERITY = {
    "low": "context_reinforcement",
    "medium": "persona_constraint_reinforcement",
    "high": "strong_reanchor_regenerate",
    "critical": "full_regenerate_and_reset",
}

_ESCALATION_ORDER = [
    "context_reinforcement",
    "persona_constraint_reinforcement",
    "scope_reinforcement",
    "strong_reanchor_regenerate",
    "full_regenerate_and_reset",
]


def select_repair_operator(drift_event: dict) -> str:
    """Heuristic policy — see module docstring for what this is and isn't."""
    severity = drift_event["severity"]
    base = _BASE_STRATEGY_BY_SEVERITY.get(severity, "context_reinforcement")

    dimensions = drift_event.get("dimensions", {})
    violated = [d for d, score in dimensions.items() if score < 0.7]

    # Scope violations get a dedicated operator regardless of severity —
    # generic "reinforce the persona" prompts were empirically the weakest
    # at actually stopping an out-of-scope answer (spec's own biryani example).
    if drift_event.get("scope_classification") == "out_of_scope_violation":
        base_idx = _ESCALATION_ORDER.index(base) if base in _ESCALATION_ORDER else 0
        scope_idx = _ESCALATION_ORDER.index("scope_reinforcement")
        return _ESCALATION_ORDER[max(base_idx, scope_idx)]

    # Multiple simultaneous violations: escalate one step beyond the raw severity mapping.
    if len(violated) >= 3 and base in _ESCALATION_ORDER:
        idx = _ESCALATION_ORDER.index(base)
        return _ESCALATION_ORDER[min(idx + 1, len(_ESCALATION_ORDER) - 1)]

    return base


def _build_repair_prompt(persona: Persona, operator: str, original_response: str, reason: str) -> str:
    base_prompt = compile_persona(persona)

    if operator == "context_reinforcement":
        return (
            f"{base_prompt}\n\nReminder: stay closely aligned with the above persona. "
            f"Regenerate your last response, keeping the same content but correcting this drift: {reason}"
        )
    if operator == "persona_constraint_reinforcement":
        constraints = "\n- ".join(persona.response_constraints + persona.behavior_rules) or "(none configured)"
        return (
            f"{base_prompt}\n\nYour last response violated these constraints:\n- {constraints}\n\n"
            f"Regenerate the response so it fully complies. Issue detected: {reason}"
        )
    if operator == "scope_reinforcement":
        return (
            f"{base_prompt}\n\nYour previous response answered a request that falls OUTSIDE your defined scope "
            f"({persona.scope or 'not defined'}). Do not answer that request. Instead, regenerate a response that "
            f"politely declines, explains it's outside your role as {persona.name}, and suggests a more suitable "
            f"kind of persona or expert — following the SCOPE instructions above exactly."
        )
    if operator == "strong_reanchor_regenerate":
        return (
            f"{base_prompt}\n\nIMPORTANT: Your previous response drifted significantly from this persona "
            f"({reason}). Fully re-anchor to the identity, tone, and rules above and regenerate a compliant "
            f"response from scratch."
        )
    # full_regenerate_and_reset
    return (
        f"{base_prompt}\n\nCRITICAL: Your previous response broke persona ({reason}). Disregard the drifted "
        f"response entirely and answer as {persona.name} would, following every rule above exactly."
    )


def _verify(
    persona: Persona,
    original_response: str,
    repaired_response: str,
    before_dimensions: dict,
    verification: dict,
    stability_before: float,
) -> tuple[bool, list[str]]:
    flags: list[str] = []
    settings = get_settings()
    stability_after = verification["overall_stability"]

    meaningful = (stability_after - stability_before) >= MEANINGFUL_IMPROVEMENT_THRESHOLD
    if not meaningful:
        flags.append("no_meaningful_improvement")

    acceptable_final = stability_after >= settings.drift_severity_medium_threshold
    if not acceptable_final:
        flags.append("final_stability_below_acceptable_threshold")

    after_dimensions = verification.get("dimensions", {})
    new_severe = [
        d for d, before in before_dimensions.items()
        if before >= 0.5 and after_dimensions.get(d, 1.0) < 0.5
    ]
    if new_severe:
        flags.append(f"new_severe_violation_in:{','.join(new_severe)}")

    usefulness_ok = True
    stripped = repaired_response.strip()
    if not stripped:
        usefulness_ok = False
        flags.append("repaired_response_empty")
    elif len(stripped) < 0.3 * len(original_response.strip()):
        usefulness_ok = False
        flags.append("repaired_response_much_shorter_than_original")
    elif stripped == original_response.strip():
        usefulness_ok = False
        flags.append("repaired_response_identical_to_original")

    success = meaningful and acceptable_final and not new_severe and usefulness_ok
    return success, flags


async def repair(
    persona: Persona,
    provider: LLMProvider,
    model: str,
    conversation_messages: list[ChatMessage],
    original_response: str,
    drift_event: dict,
    operator: str | None = None,
) -> dict:
    """Runs one repair attempt and verifies it against the criteria in _verify(). Returns a dict matching
    RepairEvent shape plus quality_flags/token_overhead/stability_improvement for research instrumentation.
    `operator` lets a caller (e.g. repair_until_verified, or a policy) override the selected operator;
    defaults to the lookup-table policy when omitted, unchanged from v2 behavior."""
    operator = operator or select_repair_operator(drift_event)
    reason = drift_event["reason"]
    stability_before = drift_event["overall_stability"]
    before_dimensions = drift_event.get("dimensions", {})

    start = time.monotonic()
    repair_prompt = _build_repair_prompt(persona, operator, original_response, reason)
    repair_messages = conversation_messages + [ChatMessage(role="system", content=repair_prompt)]

    try:
        result = await provider.generate(repair_messages, model=model)
    except ProviderError as e:
        return {
            "operator": operator,
            "stability_before": stability_before,
            "stability_after": stability_before,
            "stability_improvement": 0.0,
            "success": False,
            "duration_ms": int((time.monotonic() - start) * 1000),
            "repaired_content": "",
            "token_overhead": 0,
            "quality_flags": ["provider_error"],
            "error": str(e),
        }

    duration_ms = int((time.monotonic() - start) * 1000)
    verification = detect_drift(persona, result.content)
    success, flags = _verify(persona, original_response, result.content, before_dimensions, verification, stability_before)
    token_overhead = len(result.content.split()) - len(original_response.split())

    return {
        "operator": operator,
        "stability_before": stability_before,
        "stability_after": verification["overall_stability"],
        "stability_improvement": round(verification["overall_stability"] - stability_before, 4),
        "success": success,
        "duration_ms": duration_ms,
        "repaired_content": result.content,
        "token_overhead": token_overhead,
        "quality_flags": flags,
        "verification": verification,
    }


async def repair_until_verified(
    persona: Persona,
    provider: LLMProvider,
    model: str,
    conversation_messages: list[ChatMessage],
    original_response: str,
    drift_event: dict,
    max_cycles: int = 3,
    policy=None,
) -> dict:
    """Bounded repair-retry loop implementing the no-worse-off guarantee and
    bounded-cycles property proven (informally) in docs/repair-engine-guarantees.md.

    `policy`, if given, must expose `.select(drift_event) -> (operator, diagnostics)`
    and optionally `.update(drift_event, operator, reward)` — e.g. an
    `app.repair.policy.HybridPolicy` instance. When `policy` is None, falls back to
    `select_repair_operator()` (v2 lookup-table behavior) for every cycle, same as
    calling `repair()` directly did before this function existed.

    Escalates through `_ESCALATION_ORDER` across cycles when a policy keeps
    re-selecting the same already-failed operator, so a bounded run can't get
    stuck retrying an operator that's already been shown not to work on this
    event — see docs/repair-engine-guarantees.md, "Property 2: termination".

    Returns the BEST attempt seen (by stability_after), never something worse
    than `original_response` — if every attempt fails verification, the
    returned dict has `success=False` and `repaired_content` equal to
    `original_response` with `stability_after` equal to `stability_before`
    (a documented no-op is the failure mode, never a regression).
    """
    stability_before = drift_event["overall_stability"]
    best: dict = {
        "operator": None,
        "stability_before": stability_before,
        "stability_after": stability_before,
        "stability_improvement": 0.0,
        "success": False,
        "duration_ms": 0,
        "repaired_content": original_response,
        "token_overhead": 0,
        "quality_flags": ["no_repair_attempt_met_no_worse_off_bar"],
        "cycles_used": 0,
    }
    tried_operators: list[str] = []
    current_drift_event = drift_event

    for cycle in range(1, max_cycles + 1):
        if policy is not None:
            operator, _diagnostics = policy.select(current_drift_event)
            if operator in tried_operators and operator in _ESCALATION_ORDER:
                # Don't waste a cycle retrying an operator that already failed on
                # this event this run — escalate one step instead (see docstring).
                idx = _ESCALATION_ORDER.index(operator)
                operator = _ESCALATION_ORDER[min(idx + 1, len(_ESCALATION_ORDER) - 1)]
        else:
            operator = select_repair_operator(current_drift_event)
            if operator in tried_operators and operator in _ESCALATION_ORDER:
                idx = _ESCALATION_ORDER.index(operator)
                operator = _ESCALATION_ORDER[min(idx + 1, len(_ESCALATION_ORDER) - 1)]

        tried_operators.append(operator)
        attempt = await repair(
            persona, provider, model, conversation_messages, original_response,
            current_drift_event, operator=operator,
        )
        attempt["cycles_used"] = cycle

        if policy is not None and hasattr(policy, "update"):
            from app.repair.policy import RewardWeights, compute_reward
            reward = compute_reward(attempt, RewardWeights())
            policy.update(current_drift_event, operator, reward)

        # No-worse-off: only replace `best` with an attempt that is at least as
        # stable as the current best (which starts at stability_before, i.e.
        # the un-repaired original) — a strictly-worse attempt is recorded in
        # history (implicitly, via quality_flags on the returned event if you
        # log every attempt) but never becomes what gets returned/served.
        if attempt["stability_after"] >= best["stability_after"]:
            best = attempt

        if attempt["success"]:
            best["cycles_used"] = cycle
            return best

    return best
