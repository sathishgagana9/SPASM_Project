"""
Learned repair policy — LinUCB contextual bandit.

## What this replaces

`engine.py`'s `select_repair_operator()` is `if severity == X: use
operator Y`, with two hand-written escalation rules layered on top.
That function still exists (renamed conceptually to the "lookup
policy" below) because it's a reasonable, inspectable cold-start
default — but it is a fixed table, not something that improves from
outcomes. This module is an actual algorithmic contribution: a
LinUCB contextual bandit (Li et al., 2010, "A Contextual-Bandit
Approach to Personalized News Article Recommendation" — the standard
reference for this exact problem shape: pick one of K discrete
actions given a context vector, observe a scalar reward, improve
over time) that learns, per drift-event context, which repair
operator historically produced the best reward.

## Reward — implements spec section 10's formula directly

    repair_action = argmax(stability_improvement - latency_cost - token_cost - utility_loss)

`compute_reward()` below implements this literally, with `utility_loss`
approximated by the verification's `quality_flags` (any flag = a
utility problem, penalized). Weights on each term are configurable
(`RewardWeights`) rather than hard-coded, since the right tradeoff
(how much a second of latency should cost you vs. a point of
stability) is a genuine design choice this codebase previously never
had to make explicit, because the lookup table never optimized
anything.

## LinUCB, briefly

For each arm (operator) a, maintain A_a (d×d) and b_a (d-vector).
Predicted reward for context x: theta_a = A_a^-1 b_a, mean = theta_a·x.
Upper confidence bound: mean + alpha * sqrt(x^T A_a^-1 x). Pick
argmax over arms. After observing reward r for the chosen arm:
A_a += x x^T, b_a += r x. This explores arms whose confidence
interval is still wide (new/rare contexts) and exploits the
best-known arm as confidence narrows — appropriate here because
repair operators are genuinely different for different drift
shapes (spec's own example: scope violations need scope_reinforcement,
not generic reinforcement) and outcome data is expensive (each
update costs a real LLM repair call), so sample efficiency matters.

Pure Python matrix ops (no numpy) — d is small (~14 features, 5
arms), this is not a performance-sensitive path, and it keeps this
module dependency-free like the rest of research/evaluation/.

## Honesty status

- `LinUCBPolicy` with zero updates behaves as pure exploration
  (every arm has identical, maximally-uncertain UCB) — it does NOT
  silently fall back to being as good as the lookup table. Use
  `HybridPolicy` (below) if you want lookup-table behavior during
  cold start and a graceful handoff to the learned policy as data
  accumulates — that handoff threshold is a parameter you choose and
  should justify in the paper, not a default to trust blindly.
- This has NEVER been trained on real repair outcomes in this
  environment (no live LLM access). `research/experiments/train_repair_policy.py`
  trains it from `experiment_repair.py` result logs once you've run
  those against a real provider, and includes an offline synthetic
  smoke test that only checks the algorithm converges on a toy
  reward surface — that is a code-correctness check, NOT evidence
  the policy is good on real drift data.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

POLICY_VERSION = "raise-repair-policy-v1.0.0"

OPERATORS = [
    "context_reinforcement",
    "persona_constraint_reinforcement",
    "scope_reinforcement",
    "strong_reanchor_regenerate",
    "full_regenerate_and_reset",
]

# Context feature layout — keep in sync with featurize().
_SEVERITY_LEVELS = ["low", "medium", "high", "critical"]
FEATURE_NAMES = (
    [f"severity_{s}" for s in _SEVERITY_LEVELS]
    + ["identity", "scope", "behavior", "tone", "goals", "knowledge", "instruction", "context"]
    + ["n_violated_dims", "is_scope_violation", "bias"]
)


def featurize(drift_event: dict) -> list[float]:
    """Turns a detect_drift() result into the bandit's context vector.
    `bias` is a constant 1.0 term (standard for linear models, lets the
    model learn an arm-specific intercept)."""
    severity = drift_event.get("severity", "low")
    severity_onehot = [1.0 if severity == s else 0.0 for s in _SEVERITY_LEVELS]
    dims = drift_event.get("dimensions", {})
    dim_values = [dims.get(d, 1.0) for d in ["identity", "scope", "behavior", "tone", "goals", "knowledge", "instruction", "context"]]
    n_violated = sum(1 for v in dims.values() if v < 0.7)
    is_scope_violation = 1.0 if drift_event.get("scope_classification") == "out_of_scope_violation" else 0.0
    return severity_onehot + dim_values + [float(n_violated), is_scope_violation, 1.0]


@dataclass
class RewardWeights:
    """Weights for spec section 10's argmax formula. Defaults are a
    starting point, NOT validated — pick these to reflect your actual
    deployment priorities (a latency-sensitive product should weight
    latency_cost higher) and report whatever you used in the paper."""
    stability_weight: float = 1.0
    latency_cost_per_second: float = 0.02  # e.g. 2 extra seconds ~ 0.04 stability-points of penalty
    token_cost_per_100_tokens: float = 0.01
    utility_loss_per_quality_flag: float = 0.15


def compute_reward(repair_result: dict, weights: RewardWeights | None = None) -> float:
    """repair_result matches the dict returned by app.repair.engine.repair()."""
    w = weights or RewardWeights()
    stability_term = w.stability_weight * repair_result.get("stability_improvement", 0.0)
    latency_term = w.latency_cost_per_second * (repair_result.get("duration_ms", 0) / 1000.0)
    token_overhead = max(0, repair_result.get("token_overhead", 0))
    token_term = w.token_cost_per_100_tokens * (token_overhead / 100.0)
    utility_term = w.utility_loss_per_quality_flag * len(repair_result.get("quality_flags", []))
    return stability_term - latency_term - token_term - utility_term


# ---- tiny pure-python linear algebra (d is small; this is not a hot path) ----

def _identity(d: int) -> list[list[float]]:
    return [[1.0 if i == j else 0.0 for j in range(d)] for i in range(d)]


def _mat_vec(mat: list[list[float]], vec: list[float]) -> list[float]:
    return [sum(row[j] * vec[j] for j in range(len(vec))) for row in mat]


def _outer(vec: list[float]) -> list[list[float]]:
    return [[vi * vj for vj in vec] for vi in vec]


def _mat_add(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[a[i][j] + b[i][j] for j in range(len(a[i]))] for i in range(len(a))]


def _vec_add(a: list[float], b: list[float]) -> list[float]:
    return [ai + bi for ai, bi in zip(a, b)]


def _invert(mat: list[list[float]]) -> list[list[float]]:
    """Gauss-Jordan inversion. d ~14 here, fine in pure Python."""
    n = len(mat)
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(mat)]
    for col in range(n):
        pivot_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot_row][col]) < 1e-12:
            raise ValueError("Matrix is singular — increase regularization (ridge_lambda) or add more updates.")
        aug[col], aug[pivot_row] = aug[pivot_row], aug[col]
        pivot = aug[col][col]
        aug[col] = [v / pivot for v in aug[col]]
        for r in range(n):
            if r != col:
                factor = aug[r][col]
                aug[r] = [aug[r][k] - factor * aug[col][k] for k in range(2 * n)]
    return [row[n:] for row in aug]


@dataclass
class _Arm:
    A: list[list[float]]
    b: list[float]


@dataclass
class LinUCBPolicy:
    alpha: float = 1.0  # exploration strength — higher = more exploration
    ridge_lambda: float = 1.0
    arms: dict[str, _Arm] = field(default_factory=dict)
    n_updates: int = 0
    d: int = len(FEATURE_NAMES)

    def __post_init__(self):
        if not self.arms:
            self.arms = {
                op: _Arm(A=[row[:] for row in _scaled_identity(self.d, self.ridge_lambda)], b=[0.0] * self.d)
                for op in OPERATORS
            }

    def select(self, drift_event: dict) -> tuple[str, dict]:
        """Returns (chosen_operator, diagnostics) where diagnostics has the
        predicted mean reward and UCB per arm — useful for logging/debugging
        why the policy chose what it chose, not just the choice itself."""
        x = featurize(drift_event)
        scores = {}
        for op, arm in self.arms.items():
            A_inv = _invert(arm.A)
            theta = _mat_vec(A_inv, arm.b)
            mean = sum(t * xi for t, xi in zip(theta, x))
            confidence_width = math.sqrt(max(0.0, sum(xi * ai for xi, ai in zip(x, _mat_vec(A_inv, x)))))
            scores[op] = {"mean": round(mean, 4), "ucb": round(mean + self.alpha * confidence_width, 4)}
        chosen = max(scores, key=lambda op: scores[op]["ucb"])
        return chosen, {"scores": scores, "context_features": dict(zip(FEATURE_NAMES, x))}

    def update(self, drift_event: dict, operator: str, reward: float) -> None:
        if operator not in self.arms:
            raise ValueError(f"Unknown operator '{operator}' — must be one of {OPERATORS}")
        x = featurize(drift_event)
        arm = self.arms[operator]
        arm.A = _mat_add(arm.A, _outer(x))
        arm.b = _vec_add(arm.b, [reward * xi for xi in x])
        self.n_updates += 1

    def save(self, path: str | Path) -> None:
        payload = {
            "policy_version": POLICY_VERSION,
            "alpha": self.alpha,
            "ridge_lambda": self.ridge_lambda,
            "n_updates": self.n_updates,
            "feature_names": FEATURE_NAMES,
            "arms": {op: {"A": arm.A, "b": arm.b} for op, arm in self.arms.items()},
        }
        Path(path).write_text(json.dumps(payload, indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "LinUCBPolicy":
        data = json.loads(Path(path).read_text())
        if data.get("feature_names") != FEATURE_NAMES:
            raise ValueError("Saved policy uses a different feature layout than the current featurize() — refit.")
        policy = cls(alpha=data["alpha"], ridge_lambda=data["ridge_lambda"])
        policy.n_updates = data["n_updates"]
        policy.arms = {op: _Arm(A=v["A"], b=v["b"]) for op, v in data["arms"].items()}
        return policy


def _scaled_identity(d: int, lam: float) -> list[list[float]]:
    return [[lam if i == j else 0.0 for j in range(d)] for i in range(d)]


@dataclass
class HybridPolicy:
    """Cold-start-safe wrapper: uses the lookup-table policy
    (`app.repair.engine.select_repair_operator`) until the bandit has seen
    `warmup_updates` real outcomes, then switches to the learned policy.
    This is the policy `engine.py` should actually call in production —
    `LinUCBPolicy` alone is honest-but-unsafe before it has data."""
    bandit: LinUCBPolicy
    warmup_updates: int = 50

    def select(self, drift_event: dict) -> tuple[str, dict]:
        if self.bandit.n_updates < self.warmup_updates:
            from app.repair.engine import select_repair_operator
            return select_repair_operator(drift_event), {
                "method": "lookup_table_coldstart",
                "n_updates_so_far": self.bandit.n_updates,
                "warmup_updates": self.warmup_updates,
            }
        operator, diagnostics = self.bandit.select(drift_event)
        diagnostics["method"] = "learned_bandit"
        return operator, diagnostics

    def update(self, drift_event: dict, operator: str, reward: float) -> None:
        self.bandit.update(drift_event, operator, reward)
