"""
Numerical sanity check for the sequential conformal test-martingale.

Under the null used in this simulation, each per-turn p-value is iid Uniform(0,1),
which satisfies the conditional-super-uniform assumption required by the betting
martingale. The simulation estimates the probability of ever crossing the
anytime threshold over a finite horizon.

This is a statistical implementation check, not evidence that real LLM
conversation p-values satisfy the null assumption. Real evaluation must report
that assumption and use held-out, temporally ordered data.
"""
from __future__ import annotations

import random

from app.drift.sequential_conformal import SequentialConformalState


def validate(
    *,
    n_trials: int = 5000,
    horizon: int = 100,
    alpha: float = 0.05,
    epsilon: float = 0.5,
    seed: int = 0,
) -> dict:
    rng = random.Random(seed)
    crossed = 0
    for _ in range(n_trials):
        state = SequentialConformalState(alpha=alpha, epsilon=epsilon)
        for _t in range(horizon):
            state.update(rng.random())
            if state.alarmed:
                crossed += 1
                break
    rate = crossed / n_trials
    return {
        "n_trials": n_trials,
        "horizon": horizon,
        "alpha": alpha,
        "epsilon": epsilon,
        "observed_anytime_crossing_rate": round(rate, 4),
        "bound_target": alpha,
        "pass": rate <= alpha + 0.02,
    }


if __name__ == "__main__":
    print(validate())


def validate_empirical_system_risk_example() -> dict:
    """Reference calculation used in the paper-method checklist."""
    from app.drift.system_risk import compose_empirical_risk
    return compose_empirical_risk(5, 500, 2, 100, confidence=0.95)
