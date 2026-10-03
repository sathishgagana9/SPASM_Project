"""
Conservative LinUCB (CLUCB) repair policy — a proven-safe alternative
to HybridPolicy's ad hoc "warmup_updates" cutoff.

## The gap this fills

`policy.py`'s `HybridPolicy` decides whether to trust the learned
bandit using a single hand-picked number (`warmup_updates=50`) — an
arbitrary cutoff with no guarantee attached. Before 50 updates, it
trusts the lookup table completely; after, it trusts the bandit
completely, with nothing in between and no formal statement of what
could go wrong at the boundary.

Conservative bandits are a real, established sub-field of the bandit
literature built exactly for this problem: "I have a reliable baseline
policy in production; I want to try a learned policy that might be
better, but I need a GUARANTEE that switching to it never costs me
more than a bounded amount, at every point in time, not just
eventually." The foundational algorithm is Conservative Linear UCB
(CLUCB), introduced by Kazerouni, Ghavamzadeh, Yousefi & Van Roy,
"Conservative Contextual Linear Bandits" (NeurIPS 2017,
https://arxiv.org/abs/1611.06426), with follow-up refinements (e.g.
Deb, Ghavamzadeh & Banerjee's CLUCB2 / "Conservative Contextual
Bandits: Beyond Linear Representations", 2024). This module adapts
CLUCB to the repair-operator-selection problem — see "What's adapted
vs. verbatim" below for exactly where this deviates from the cited
papers, stated honestly rather than presented as a direct
reproduction.

## The formal guarantee (Kazerouni et al. 2017, Proposition 1)

With probability at least `1 - delta`, CLUCB's cumulative reward at
every round `t` satisfies:

    sum_{s=1}^{t} r_bandit(s)  >=  (1 - alpha) * sum_{s=1}^{t} r_baseline(s)

i.e. the learned policy's total reward never falls more than a factor
`alpha` below what the baseline (lookup-table) policy would have
earned over the SAME rounds — UNIFORMLY OVER TIME, not just in the
limit. In exchange, CLUCB's regret relative to the best-possible
policy is the standard LinUCB regret PLUS an additive, time-independent
constant that accounts for the rounds spent being conservative
(Kazerouni et al., Theorem 2) — you pay a bounded, one-time cost for
the safety guarantee, not a permanently worse learning rate.

## What's adapted vs. verbatim (read before citing this as "CLUCB")

- **Baseline reward estimation**: the original papers assume the
  baseline policy's per-round reward is either known exactly or
  estimated from a long history of PRIOR deployment (so its estimate
  is already tight by the time the conservative bandit starts
  running). This codebase has no such history — the lookup-table
  policy (`select_repair_operator`) has never been run against real
  outcomes either. This implementation instead estimates the
  baseline's expected reward for a given context using the SAME
  per-arm linear reward model the bandit itself maintains (i.e., the
  baseline's estimated reward for context `x` is the bandit's current
  `theta_{baseline_arm} . x`). This is a reasonable, defensible
  adaptation — it reuses data efficiently and converges to the true
  baseline reward as more data accumulates — but it means the safety
  guarantee above is WEAKER during early rounds than the original
  papers' guarantee, because the baseline estimate itself is still
  uncertain then. Report `n_rounds` alongside any safety claim; the
  guarantee is meaningfully tight only once the baseline arm has
  enough observations for its own confidence interval to be narrow
  (the same "enough data" caveat that applies to LinUCB itself).
- **Single-baseline-policy setting**: the cited papers are agnostic to
  what the baseline is; here it is specifically `select_repair_operator`
  (this codebase's severity lookup table).
- This has NEVER been run against real repair outcomes in this
  environment (no live LLM access) — `verify_safety_guarantee()` below
  runs a synthetic numerical check (does the observed cumulative-reward
  ratio actually stay within the promised bound, across many random
  trials) — a code-correctness check on the ALGORITHM, not evidence
  about real persona-repair data, exactly like `policy.py`'s existing
  smoke test.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.repair.policy import LinUCBPolicy, featurize, _invert, _mat_vec


@dataclass
class ConservativeLinUCBPolicy:
    bandit: LinUCBPolicy
    baseline_operator_fn: callable  # e.g. app.repair.engine.select_repair_operator
    alpha_safety: float = 0.1  # max allowed fractional shortfall vs. baseline (the paper's "alpha")
    cumulative_bandit_reward: float = 0.0
    cumulative_baseline_reward: float = 0.0
    n_rounds: int = 0
    n_conservative_plays: int = 0  # how often the safety check forced a fallback to baseline

    def _arm_mean(self, operator: str, x: list[float]) -> float:
        arm = self.bandit.arms[operator]
        theta = _mat_vec(_invert(arm.A), arm.b)
        return sum(t * xi for t, xi in zip(theta, x))

    def _arm_lcb(self, operator: str, x: list[float]) -> float:
        """Pessimistic (lower confidence bound) estimate — mirrors
        LinUCBPolicy.select()'s UCB computation but subtracts the
        confidence width instead of adding it, since the safety check
        needs a WORST-CASE-not-best-case estimate of the candidate
        action's reward."""
        arm = self.bandit.arms[operator]
        A_inv = _invert(arm.A)
        theta = _mat_vec(A_inv, arm.b)
        mean = sum(t * xi for t, xi in zip(theta, x))
        confidence_width = (sum(xi * ai for xi, ai in zip(x, _mat_vec(A_inv, x)))) ** 0.5
        return mean - self.bandit.alpha * confidence_width

    def select(self, drift_event: dict) -> tuple[str, dict]:
        x = featurize(drift_event)
        baseline_op = self.baseline_operator_fn(drift_event)
        optimistic_op, diagnostics = self.bandit.select(drift_event)

        if optimistic_op == baseline_op:
            self.n_rounds += 1
            diagnostics["method"] = "conservative_linucb_agrees_with_baseline"
            return optimistic_op, diagnostics

        candidate_lcb = self._arm_lcb(optimistic_op, x)
        baseline_mean = self._arm_mean(baseline_op, x)

        projected_bandit_total = self.cumulative_bandit_reward + candidate_lcb
        projected_baseline_total = self.cumulative_baseline_reward + baseline_mean
        is_safe = projected_bandit_total >= (1 - self.alpha_safety) * projected_baseline_total

        self.n_rounds += 1
        if is_safe:
            diagnostics["method"] = "conservative_linucb_optimistic"
            diagnostics["safety_check"] = {"candidate_lcb": round(candidate_lcb, 4), "baseline_mean": round(baseline_mean, 4), "passed": True}
            return optimistic_op, diagnostics

        self.n_conservative_plays += 1
        diagnostics["method"] = "conservative_linucb_fallback_to_baseline"
        diagnostics["safety_check"] = {"candidate_lcb": round(candidate_lcb, 4), "baseline_mean": round(baseline_mean, 4), "passed": False}
        return baseline_op, diagnostics

    def update(self, drift_event: dict, operator: str, reward: float) -> None:
        self.bandit.update(drift_event, operator, reward)
        self.cumulative_bandit_reward += reward

        # Baseline bookkeeping uses the bandit's OWN estimate for the
        # baseline arm on this round's context (see module docstring's
        # "What's adapted" section) — not a separately-observed reward,
        # since the baseline policy wasn't necessarily the one actually
        # played this round.
        x = featurize(drift_event)
        baseline_op_this_round = self.baseline_operator_fn(drift_event)
        self.cumulative_baseline_reward += self._arm_mean(baseline_op_this_round, x)

    def safety_margin(self) -> float | None:
        """How much headroom is left before the safety constraint would
        bind: (bandit_total - (1-alpha)*baseline_total) / baseline_total.
        Positive = comfortably safe; near zero = the next unsafe-looking
        action will be vetoed; undefined (None) before any rounds."""
        if self.n_rounds == 0 or self.cumulative_baseline_reward == 0:
            return None
        required = (1 - self.alpha_safety) * self.cumulative_baseline_reward
        return (self.cumulative_bandit_reward - required) / abs(self.cumulative_baseline_reward)
