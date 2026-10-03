"""
Cost-sensitive Bayes-optimal gating threshold.

## The gap this fills

Every threshold in this codebase so far has been a hand-picked number
with a comment like "PROVISIONAL — not calibrated" (see
`app/drift/scoring.py`'s `THRESHOLD_VERSION = "manual-v1"`, and
`scope.py`'s `OUT_OF_SCOPE_THRESHOLD = 0.06`). That is an honest way to
flag an uncalibrated constant, but it's still just a guess. Standard
Bayesian decision theory gives a DERIVED, defensible threshold once you
state two things explicitly: (1) the classifier's confidence is a
genuine probability estimate, and (2) the relative COST of a false
accept (letting an actual violation through) vs. a false reject
(blocking a legitimate request) is a real design choice you're willing
to state a number for. This module makes that derivation and that cost
tradeoff EXPLICIT and adjustable, rather than folding them into an
unstated constant.

## The math

Let `p = P(request is actually out-of-scope or a switch attempt |
classifier's evidence)` — this project already asks the classifier to
report exactly this as `confidence` when it says `in_scope=False` or
`persona_switch_attempt=True` (see `intent_classifier.py`). Let:

  - `C_FA` = cost of a False Accept (the gate lets an actual violation
    through — generates unauthorized content).
  - `C_FR` = cost of a False Reject (the gate blocks a legitimate
    request — a false-positive refusal, annoying but not unsafe).

The Bayes-optimal decision rule (minimizing expected cost; this is the
standard Bayes risk / Neyman-Pearson-adjacent result taught in any
detection-theory text, e.g. Kay, "Fundamentals of Statistical Signal
Processing: Detection Theory", Ch. 3) is: BLOCK the request if and only
if

    p >= C_FR / (C_FA + C_FR)

i.e. the optimal threshold is NOT 0.5 unless the two costs are equal —
it shifts toward 0 as false accepts get costlier relative to false
rejects (block more readily), and toward 1 as false rejects get
costlier (block less readily, tolerate more risk to stay helpful).
`bayes_optimal_threshold()` below just IS this formula; the value is
this module's contribution is making the tradeoff explicit and giving
the sensitivity-analysis tooling to justify a specific choice of
`C_FA`/`C_FR`, not the formula itself (which is textbook).

## Per-persona-risk-tier cost scaling

Not every persona should use the same `C_FA`/`C_FR` ratio — the spec's
own examples imply this: a Doctor persona giving unauthorized medical
content is a worse false-accept than a Chef persona giving an
unauthorized coding tip. `RISK_TIER_COST_MULTIPLIERS` below lets
`C_FA` scale by the persona's declared risk tier, so higher-stakes
personas get a lower (more block-happy) threshold automatically,
DERIVED from the same formula rather than hand-tuned per persona.

## Honest status

- This assumes the classifier's `confidence` field is a genuine,
  reasonably-calibrated probability. `intent_classifier.py` already
  states this is NOT verified (the confidence is the model's
  self-reported number, unvalidated against ground truth). This
  module's formula is only as trustworthy as that calibration — see
  `research/evaluation/calibration.py` (Brier score / ECE) for how to
  actually check this once real classifier outputs exist. Until then,
  treat the derived threshold as "correct given the stated costs and
  an assumption of calibration," not as an empirically-validated
  number.
- The specific `C_FA`/`C_FR` values below are ILLUSTRATIVE — actual
  values should reflect a real product/research decision about
  relative harms, which nobody has made for this project yet. Ship
  the formula and the sensitivity-analysis tool, not a specific
  "correct" number.
"""
from __future__ import annotations

from dataclasses import dataclass

# Illustrative default costs — see module docstring. Override per deployment.
DEFAULT_COST_FALSE_ACCEPT = 3.0   # letting a violation through
DEFAULT_COST_FALSE_REJECT = 1.0   # blocking a legitimate request

# Multiplies C_FA by declared persona risk tier — higher stakes, lower
# (more block-happy) threshold. Illustrative, not empirically derived.
RISK_TIER_COST_MULTIPLIERS = {
    "low": 1.0,       # e.g. Chef, Customer Support
    "medium": 2.0,    # e.g. Teacher, Research Assistant, Coding Expert
    "high": 4.0,      # e.g. Lawyer, Financial Advisor
    "critical": 8.0,  # e.g. Doctor
}


def bayes_optimal_threshold(cost_false_accept: float, cost_false_reject: float) -> float:
    if cost_false_accept <= 0 or cost_false_reject <= 0:
        raise ValueError("Costs must be strictly positive — a zero or negative cost makes the decision rule degenerate.")
    return cost_false_reject / (cost_false_accept + cost_false_reject)


def threshold_for_risk_tier(
    risk_tier: str, base_cost_false_accept: float = DEFAULT_COST_FALSE_ACCEPT,
    cost_false_reject: float = DEFAULT_COST_FALSE_REJECT,
) -> float:
    if risk_tier not in RISK_TIER_COST_MULTIPLIERS:
        raise ValueError(f"Unknown risk tier '{risk_tier}' — must be one of {list(RISK_TIER_COST_MULTIPLIERS)}")
    scaled_cost_fa = base_cost_false_accept * RISK_TIER_COST_MULTIPLIERS[risk_tier]
    return bayes_optimal_threshold(scaled_cost_fa, cost_false_reject)


@dataclass
class GateDecision:
    should_block: bool
    threshold_used: float
    confidence: float
    risk_tier: str


def decide(confidence_it_is_a_violation: float, risk_tier: str = "medium") -> GateDecision:
    """The actual decision function a caller would use in place of a bare
    `if not classification.in_scope:` check — makes the threshold and its
    provenance (which risk tier, which cost ratio) explicit in the
    returned object, so a logged decision is auditable after the fact."""
    threshold = threshold_for_risk_tier(risk_tier)
    return GateDecision(
        should_block=confidence_it_is_a_violation >= threshold,
        threshold_used=threshold, confidence=confidence_it_is_a_violation, risk_tier=risk_tier,
    )


def sensitivity_analysis(cost_ratios: list[float] | None = None) -> list[dict]:
    """Sweeps the cost ratio C_FA/C_FR (holding C_FR=1) and reports the
    resulting threshold — this table is what should actually go in a
    paper's methods section to justify a chosen operating point, rather
    than asserting one number as correct."""
    ratios = cost_ratios or [0.5, 1.0, 2.0, 3.0, 4.0, 8.0, 16.0]
    return [
        {"cost_false_accept_over_reject_ratio": r, "cost_false_accept": r, "cost_false_reject": 1.0,
         "bayes_optimal_threshold": round(bayes_optimal_threshold(r, 1.0), 4)}
        for r in ratios
    ]
