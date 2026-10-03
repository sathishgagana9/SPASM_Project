"""
End-to-end risk ledger for the SPASM++ detection/repair loop.

The ledger deliberately separates three quantities that are often conflated:

1. detector false-alarm budget alpha_D;
2. repair safety-failure confidence delta_R (or an empirically estimated
   repair failure probability);
3. the resulting conservative system-level risk budget.

If the two failure events are covered by valid probability bounds, the union
bound gives

    P(detector false alarm OR repair safety failure)
       <= alpha_D + delta_R.

This is a conservative composition, not an independence assumption. It is
only a valid *guarantee* when the component bounds have actually been
established under their stated assumptions. Otherwise the result is a
planning/ledger number and must be labeled empirical or budgeted, not formal.
"""
from __future__ import annotations

from dataclasses import dataclass

SYSTEM_RISK_VERSION = "spasm-system-risk-v1.0.0"


@dataclass(frozen=True)
class SystemRiskBudget:
    detector_alpha: float
    repair_delta: float
    system_failure_bound: float
    guarantee_confidence: float
    composition: str = "union_bound"
    formal: bool = False

    def as_dict(self) -> dict:
        return {
            "version": SYSTEM_RISK_VERSION,
            "detector_alpha": self.detector_alpha,
            "repair_delta": self.repair_delta,
            "system_failure_bound": self.system_failure_bound,
            "guarantee_confidence": self.guarantee_confidence,
            "composition": self.composition,
            "formal": self.formal,
            "interpretation": (
                "Conservative end-to-end probability bound under the supplied component assumptions."
                if self.formal else
                "Budget/diagnostic only: component guarantees have not yet been empirically or theoretically established for this deployment."
            ),
        }


def compose_system_risk(
    detector_alpha: float,
    repair_delta: float,
    *,
    component_guarantees_established: bool = False,
) -> SystemRiskBudget:
    """Compose detector and repair failure budgets using the union bound."""
    if not 0.0 <= detector_alpha <= 1.0:
        raise ValueError("detector_alpha must be in [0, 1]")
    if not 0.0 <= repair_delta <= 1.0:
        raise ValueError("repair_delta must be in [0, 1]")
    bound = min(1.0, detector_alpha + repair_delta)
    return SystemRiskBudget(
        detector_alpha=detector_alpha,
        repair_delta=repair_delta,
        system_failure_bound=bound,
        guarantee_confidence=1.0 - bound,
        formal=component_guarantees_established,
    )


def clopper_pearson_upper(failures: int, trials: int, confidence: float = 0.95) -> float:
    """Exact one-sided binomial upper confidence bound.

    Used for empirical end-to-end risk reporting. This is a confidence bound
    on an observed failure probability, not a claim that the deployment
    process itself satisfies iid assumptions.
    """
    if trials <= 0 or failures < 0 or failures > trials:
        raise ValueError("Require trials > 0 and 0 <= failures <= trials")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    try:
        from scipy.stats import beta
    except ImportError as exc:
        raise RuntimeError("Install scipy to compute exact empirical risk bounds") from exc
    if failures == trials:
        return 1.0
    alpha = 1.0 - confidence
    return float(beta.ppf(1.0 - alpha, failures + 1, trials - failures))


def compose_empirical_risk(
    detector_false_alarms: int,
    detector_tests: int,
    repair_safety_failures: int,
    repair_trials: int,
    *,
    confidence: float = 0.95,
) -> dict:
    """Turn held-out observed failures into a conservative system risk bound.

    The component rates are first bounded separately with exact one-sided
    binomial intervals, then composed with the union bound. This avoids treating
    the two failure modes as independent.
    """
    d_upper = clopper_pearson_upper(detector_false_alarms, detector_tests, confidence)
    r_upper = clopper_pearson_upper(repair_safety_failures, repair_trials, confidence)
    budget = compose_system_risk(d_upper, r_upper, component_guarantees_established=False)
    return {
        **budget.as_dict(),
        "confidence_level": confidence,
        "detector_observed": {"failures": detector_false_alarms, "trials": detector_tests, "upper_bound": d_upper},
        "repair_observed": {"failures": repair_safety_failures, "trials": repair_trials, "upper_bound": r_upper},
        "interpretation": "Empirical conservative upper bound from held-out data; not a distribution-free guarantee for arbitrary future conversations.",
    }
