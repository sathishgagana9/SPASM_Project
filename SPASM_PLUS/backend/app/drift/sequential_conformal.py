"""
Sequential / anytime-valid conformal evidence for persona-drift monitoring.

This module does NOT claim that ordinary conformal p-values are automatically
anytime-valid under arbitrary conversational dependence.  The test-martingale
statement requires conditional super-uniform p-values (or another valid
sequential calibration construction).  The implementation therefore exposes
that assumption explicitly and is intended to aggregate valid per-turn
p-values produced by a conformal detector.

For p_t in [0,1], the power betting factor

    g_epsilon(p) = epsilon * p ** (epsilon - 1), 0 < epsilon < 1

has expectation 1 when p is Uniform(0,1).  The product of these factors is a
nonnegative test martingale under the conditional-super-uniform null.  We use
log-evidence for numerical stability and alarm when the martingale exceeds
1 / alpha.  A conservative optional reset is provided after a confirmed
intervention; resetting starts a new monitoring episode and its validity must
be interpreted episode-by-episode.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

SEQUENTIAL_CONFORMAL_VERSION = "spasm-seq-conformal-v1.0.0"


@dataclass
class SequentialConformalState:
    """State of one monitoring episode."""

    alpha: float = 0.05
    epsilon: float = 0.5
    log_e_value: float = 0.0
    n_turns: int = 0
    max_log_e_value: float = 0.0
    alarmed: bool = False
    alarm_turn: int | None = None
    p_values: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 < self.alpha < 1.0:
            raise ValueError("alpha must be in (0, 1)")
        if not 0.0 < self.epsilon < 1.0:
            raise ValueError("epsilon must be in (0, 1)")

    @property
    def e_value(self) -> float:
        # Avoid overflow in normal use. Once the threshold is crossed the
        # exact value is less important than the evidence level.
        if self.log_e_value >= 700:
            return float("inf")
        return math.exp(self.log_e_value)

    @property
    def threshold_e_value(self) -> float:
        return 1.0 / self.alpha

    @property
    def evidence_ratio(self) -> float:
        """E_t / (1/alpha); >= 1 means the anytime threshold is crossed."""
        if self.log_e_value >= 700:
            return float("inf")
        return self.e_value / self.threshold_e_value

    def update(self, p_value: float) -> dict:
        """Consume one valid per-turn conformal p-value.

        The p-value is clipped only at machine-safe endpoints. The clipping is
        not a statistical correction; it prevents log(0) and infinite factors
        from destabilising the implementation.
        """
        if not 0.0 <= p_value <= 1.0:
            raise ValueError("p_value must be in [0, 1]")
        p = min(max(float(p_value), 1e-12), 1.0)
        log_factor = math.log(self.epsilon) + (self.epsilon - 1.0) * math.log(p)
        self.log_e_value += log_factor
        self.n_turns += 1
        self.max_log_e_value = max(self.max_log_e_value, self.log_e_value)
        self.p_values.append(p)

        crossed = self.log_e_value >= math.log(1.0 / self.alpha)
        if crossed and not self.alarmed:
            self.alarmed = True
            self.alarm_turn = self.n_turns

        return self.snapshot()

    def snapshot(self) -> dict:
        return {
            "version": SEQUENTIAL_CONFORMAL_VERSION,
            "alpha": self.alpha,
            "epsilon": self.epsilon,
            "n_turns": self.n_turns,
            "e_value": self.e_value,
            "evidence_ratio": self.evidence_ratio,
            "alarmed": self.alarmed,
            "alarm_turn": self.alarm_turn,
            "max_e_value": math.exp(self.max_log_e_value) if self.max_log_e_value < 700 else float("inf"),
            "p_values_seen": len(self.p_values),
            "validity_assumption": "conditional_super_uniform_per_turn_p_values_under_the_null",
        }

    def reset(self) -> None:
        """Start a fresh monitoring episode.

        The reset is explicit because a repair/intervention changes the data
        generating process. Any end-to-end guarantee must account for the
        number and timing of such episodes.
        """
        self.log_e_value = 0.0
        self.n_turns = 0
        self.max_log_e_value = 0.0
        self.alarmed = False
        self.alarm_turn = None
        self.p_values.clear()


def update_sequential_evidence(state: SequentialConformalState, p_value: float) -> dict:
    """Functional convenience wrapper used by experiment scripts."""
    return state.update(p_value)
