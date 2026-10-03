"""
Stress-tests ConservativeLinUCBPolicy's safety guarantee numerically —
does cumulative_bandit_reward actually stay within (1-alpha) of
cumulative_baseline_reward, uniformly over time, INCLUDING in a scenario
deliberately designed to tempt the optimistic (unconstrained) LinUCB
component into an unsafe choice?

This is a code-correctness check on the ALGORITHM (does the safety
mechanism actually veto unsafe actions when it should), not evidence
about real repair outcomes — see safe_policy.py's module docstring,
especially "What's adapted vs. verbatim", for why the guarantee is
expected to be WEAKER during early rounds here than in the cited papers
(baseline reward is estimated, not known) — this script explicitly
measures and reports that early-round weakness rather than hiding it.

Usage: python3 safe_bandit_validation.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from app.repair.policy import LinUCBPolicy, OPERATORS  # noqa: E402
from app.repair.safe_policy import ConservativeLinUCBPolicy  # noqa: E402


def make_event(rng: random.Random, decoy_active: bool) -> dict:
    severity = rng.choice(["low", "medium", "high", "critical"])
    dims = {d: rng.uniform(0.3, 1.0) for d in
            ["identity", "scope", "behavior", "tone", "goals", "knowledge", "instruction", "context"]}
    return {"severity": severity, "dimensions": dims, "scope_classification": "in_scope", "_decoy_active": decoy_active}


def true_reward(rng: random.Random, event: dict, operator: str, decoy_operator: str, phase: int) -> float:
    """The baseline-equivalent arm ('persona_constraint_reinforcement', a
    reasonable generic choice) earns a steady 0.5. In PHASE 1 (rounds
    0-150), a DECOY arm is inflated to look like the best option (0.9) to
    force LinUCB to prefer it optimistically. In PHASE 2 (rounds 150+),
    the decoy's true reward crashes to 0.05 — well below baseline — which
    is exactly the scenario an UNCONSTRAINED bandit would keep exploiting
    for a while (it takes time for LinUCB's estimate to catch up), and
    exactly what the conservative safety check exists to bound the damage
    from."""
    baseline_op = "persona_constraint_reinforcement"
    if operator == baseline_op:
        return 0.5 + rng.gauss(0, 0.05)
    if operator == decoy_operator:
        return (0.9 if phase == 1 else 0.05) + rng.gauss(0, 0.05)
    return 0.2 + rng.gauss(0, 0.05)  # other arms are just mediocre


def run(n_rounds: int = 400, alpha_safety: float = 0.1, seed: int = 3) -> dict:
    rng = random.Random(seed)
    decoy_operator = "strong_reanchor_regenerate"

    def baseline_fn(event: dict) -> str:
        return "persona_constraint_reinforcement"

    bandit = LinUCBPolicy(alpha=1.5)
    policy = ConservativeLinUCBPolicy(bandit=bandit, baseline_operator_fn=baseline_fn, alpha_safety=alpha_safety)

    # Unconstrained comparison arm, run in parallel on the SAME reward
    # sequence, to show what would have happened WITHOUT the safety check.
    unconstrained = LinUCBPolicy(alpha=1.5)
    unconstrained_cumulative = 0.0
    baseline_only_cumulative = 0.0

    violation_rounds = []
    trace = []

    for i in range(n_rounds):
        phase = 1 if i < n_rounds // 2 else 2
        event = make_event(rng, decoy_active=True)

        chosen_op, _ = policy.select(event)
        reward = true_reward(rng, event, chosen_op, decoy_operator, phase)
        policy.update(event, chosen_op, reward)

        unconstrained_op, _ = unconstrained.select(event)
        unconstrained_reward = true_reward(rng, event, unconstrained_op, decoy_operator, phase)
        unconstrained.update(event, unconstrained_op, unconstrained_reward)
        unconstrained_cumulative += unconstrained_reward

        baseline_only_cumulative += true_reward(rng, event, baseline_fn(event), decoy_operator, phase)

        required = (1 - alpha_safety) * policy.cumulative_baseline_reward
        satisfied = policy.cumulative_bandit_reward >= required - 1e-9
        if not satisfied:
            violation_rounds.append(i)

        if i % 40 == 0 or i == n_rounds - 1:
            trace.append({
                "round": i, "phase": phase,
                "cumulative_bandit": round(policy.cumulative_bandit_reward, 2),
                "cumulative_baseline_est": round(policy.cumulative_baseline_reward, 2),
                "required_floor": round(required, 2),
                "n_conservative_plays_so_far": policy.n_conservative_plays,
            })

    return {
        "n_rounds": n_rounds, "alpha_safety": alpha_safety,
        "final_cumulative_conservative_bandit": round(policy.cumulative_bandit_reward, 2),
        "final_cumulative_baseline_estimate": round(policy.cumulative_baseline_reward, 2),
        "final_cumulative_unconstrained_bandit": round(unconstrained_cumulative, 2),
        "final_cumulative_pure_baseline_realized": round(baseline_only_cumulative, 2),
        "n_conservative_plays": policy.n_conservative_plays,
        "n_rounds_total": policy.n_rounds,
        "violation_rounds": violation_rounds,
        "violation_rate": round(len(violation_rounds) / n_rounds, 4),
        "trace": trace,
    }


def main():
    report = run()
    print(f"n_rounds={report['n_rounds']}, alpha_safety={report['alpha_safety']}\n")
    print("Round-by-round trace:")
    for row in report["trace"]:
        print(f"  round={row['round']:4d} phase={row['phase']}  bandit_cum={row['cumulative_bandit']:8.2f}  "
              f"baseline_est_cum={row['cumulative_baseline_est']:8.2f}  required_floor={row['required_floor']:8.2f}  "
              f"conservative_plays_so_far={row['n_conservative_plays_so_far']}")

    print(f"\nFinal cumulative reward — conservative bandit:     {report['final_cumulative_conservative_bandit']}")
    print(f"Final cumulative reward — baseline estimate:       {report['final_cumulative_baseline_estimate']}")
    print(f"Final cumulative reward — UNCONSTRAINED bandit:    {report['final_cumulative_unconstrained_bandit']}")
    print(f"Final cumulative reward — pure baseline (realized):{report['final_cumulative_pure_baseline_realized']}")
    print(f"\nConservative fallback triggered on {report['n_conservative_plays']}/{report['n_rounds_total']} rounds.")
    print(f"Safety-constraint violation rate: {report['violation_rate']} ({len(report['violation_rounds'])} rounds)")

    if report["violation_rounds"]:
        print(f"\nNOTE (expected, per module docstring): violations, if any, should cluster in EARLY rounds "
              f"before the baseline arm's own reward estimate has converged — that's the honestly-disclosed "
              f"weaker guarantee from estimating rather than knowing the baseline reward. First violation at "
              f"round {report['violation_rounds'][0]}, last at round {report['violation_rounds'][-1]}.")
    else:
        print("\nNo safety-constraint violations observed at any round in this run.")

    print("\nKey comparison: does the UNCONSTRAINED bandit take a bigger hit than the CONSERVATIVE one during "
          "the phase-2 decoy crash? Compare the two 'Final cumulative reward' lines above.")


if __name__ == "__main__":
    main()
