"""
Trains `app.repair.policy.LinUCBPolicy` from real repair-experiment
logs, and includes a synthetic smoke test that validates the
algorithm converges on a KNOWN, hand-constructed reward surface
(same idea as the doctest-style check in policy.py's module
docstring). Those are two different things — keep them separate when
you cite results:

- `--smoke-test`: runs entirely offline, no real data needed, checks
  the bandit algorithm is implemented correctly (arm selection tracks
  a known-best arm on synthetic reward). This is a CODE-CORRECTNESS
  check. Safe to run right now, in this environment.
- `--train <path-or-glob>`: trains on REAL `experiment_repair.py`
  output (`research/results/raw/experiment_repair_*.json`) — this
  needs you to have actually run that experiment against a live
  provider first (see EXPERIMENTS.md). This produces a policy that
  reflects real outcomes; the smoke test does not and is not a
  substitute for this.

Usage:
    python3 train_repair_policy.py --smoke-test
    python3 train_repair_policy.py --train "../results/raw/experiment_repair_*.json" --out policy_weights.json
"""
import argparse
import glob
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))


def run_smoke_test(n_trials: int = 400, seed: int = 1) -> dict:
    """Synthetic ground truth: scope-violation events get max reward from
    scope_reinforcement; everything else gets max reward from
    persona_constraint_reinforcement. Reports what fraction of the LAST 50
    selections match the known-best arm — should be high (this is a
    code-correctness check on the algorithm, not evidence about real drift
    repair, see module docstring)."""
    from app.repair.policy import LinUCBPolicy

    rng = random.Random(seed)

    def make_event(is_scope_violation: bool) -> dict:
        dims = {
            "identity": 1.0, "scope": 0.2 if is_scope_violation else 0.9, "behavior": 0.9,
            "tone": 1.0, "goals": 1.0, "knowledge": 1.0, "instruction": 1.0, "context": 1.0,
        }
        return {
            "severity": "high", "dimensions": dims,
            "scope_classification": "out_of_scope_violation" if is_scope_violation else "in_scope",
        }

    def true_reward(event: dict, operator: str) -> float:
        is_scope = event["scope_classification"] == "out_of_scope_violation"
        best = "scope_reinforcement" if is_scope else "persona_constraint_reinforcement"
        base = 0.8 if operator == best else 0.2
        return base + rng.gauss(0, 0.05)

    policy = LinUCBPolicy(alpha=1.0)
    correct = 0
    window = min(50, n_trials)
    for i in range(n_trials):
        is_scope = rng.random() < 0.5
        event = make_event(is_scope)
        operator, _ = policy.select(event)
        reward = true_reward(event, operator)
        policy.update(event, operator, reward)
        if i >= n_trials - window:
            best = "scope_reinforcement" if is_scope else "persona_constraint_reinforcement"
            correct += int(operator == best)

    accuracy = correct / window
    result = {
        "n_trials": n_trials, "last_window_accuracy_vs_known_best_arm": round(accuracy, 4),
        "passed": accuracy >= 0.85,
    }
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        print("SMOKE TEST FAILED — the bandit did not converge to the known-best arm. "
              "Check policy.py for a regression before trusting it on real data.", file=sys.stderr)
        sys.exit(1)
    print("Smoke test passed — algorithm converges correctly on synthetic reward. "
          "This does NOT mean the policy will be good on real drift data; train on real logs for that.")
    return result


def load_repair_records(pattern: str) -> list[dict]:
    records = []
    for path in glob.glob(pattern):
        with open(path) as f:
            payload = json.load(f)
        records.extend(payload.get("records", []))
    return records


def train_from_logs(pattern: str, out_path: str, alpha: float = 1.0) -> dict:
    from app.repair.policy import LinUCBPolicy, RewardWeights, compute_reward

    records = load_repair_records(pattern)
    if not records:
        print(f"No records found matching '{pattern}'. Run experiment_repair.py first — "
              "see EXPERIMENTS.md — this trainer has nothing to train on without real outcomes.")
        sys.exit(1)

    missing_context = [r for r in records if "drift_event" not in r]
    if missing_context:
        print(
            f"WARNING: {len(missing_context)}/{len(records)} records have no 'drift_event' field, "
            "so they can't be used as bandit training context (the policy needs the pre-repair "
            "dimension scores, not just the outcome). experiment_repair.py was updated to log "
            "'drift_event' — re-run it if your logs predate that change. Skipping these records."
        )

    usable = [r for r in records if "drift_event" in r]
    policy = LinUCBPolicy(alpha=alpha)
    for r in usable:
        reward = compute_reward(r, RewardWeights())
        policy.update(r["drift_event"], r["operator"], reward)

    policy.save(out_path)
    report = {
        "n_records_total": len(records), "n_records_used": len(usable),
        "n_updates": policy.n_updates, "saved_to": out_path,
    }
    print(json.dumps(report, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true", help="Run the offline algorithm-correctness check.")
    parser.add_argument("--train", type=str, default=None, help="Glob pattern for experiment_repair.py result JSON files.")
    parser.add_argument("--out", type=str, default="repair_policy_weights.json")
    parser.add_argument("--alpha", type=float, default=1.0, help="LinUCB exploration strength.")
    args = parser.parse_args()

    if args.smoke_test:
        run_smoke_test()
    elif args.train:
        train_from_logs(args.train, args.out, args.alpha)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
