"""
Validates the conformal drift test's core mathematical claim: under the
null (new point IS exchangeable with the calibration set), the false-alarm
rate at threshold alpha is at most alpha — for ANY embedding distribution,
not just a convenient one.

This is a NUMERICAL SANITY CHECK on the statistics (does the code correctly
implement the guarantee Vovk et al. prove exists), not a claim about real
LLM persona responses — see app/drift/conformal.py's docstring for that
distinction. Run this before citing the false-alarm-rate guarantee in any
write-up, and re-run it if conformal.py's nonconformity measure changes.

Usage: python3 conformal_validation.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from app.drift.conformal import _knn_nonconformity  # noqa: E402


def run_trial(rng: random.Random, n_calibration: int, dim: int, k: int) -> float:
    """One trial under the null: calibration set AND the 'new' point are
    drawn from the exact same distribution (here, independent standard
    Gaussian coordinates — deliberately a distribution with no special
    structure, since the guarantee is supposed to hold regardless).
    Returns the p-value computed the same way conformal_drift_test does,
    without needing real text/embeddings for this pure-statistics check."""
    calib = [[rng.gauss(0, 1) for _ in range(dim)] for _ in range(n_calibration)]
    new_point = [rng.gauss(0, 1) for _ in range(dim)]  # same distribution — this IS the null

    null_scores = []
    for i in range(len(calib)):
        others = calib[:i] + calib[i + 1:]
        null_scores.append(_knn_nonconformity(calib[i], others, k))
    new_score = _knn_nonconformity(new_point, calib, k)

    n = len(null_scores)
    n_at_least_as_extreme = sum(1 for s in null_scores if s >= new_score)
    return (1 + n_at_least_as_extreme) / (n + 1)


def validate(n_trials: int = 5000, n_calibration: int = 20, dim: int = 8, k: int = 3, seed: int = 0) -> dict:
    rng = random.Random(seed)
    p_values = [run_trial(rng, n_calibration, dim, k) for _ in range(n_trials)]

    report = {"n_trials": n_trials, "n_calibration": n_calibration, "dim": dim, "k": k}
    for alpha in (0.01, 0.05, 0.10, 0.20):
        false_alarm_rate = sum(1 for p in p_values if p < alpha) / n_trials
        report[f"alpha={alpha}"] = {
            "observed_false_alarm_rate": round(false_alarm_rate, 4),
            "guarantee_satisfied": false_alarm_rate <= alpha + 0.02,  # small numerical/simulation tolerance
        }
    return report


def main():
    report = validate()
    print(f"n_trials={report['n_trials']}, n_calibration={report['n_calibration']}, "
          f"dim={report['dim']}, k={report['k']}\n")
    all_ok = True
    for alpha in (0.01, 0.05, 0.10, 0.20):
        r = report[f"alpha={alpha}"]
        status = "PASS" if r["guarantee_satisfied"] else "FAIL"
        if not r["guarantee_satisfied"]:
            all_ok = False
        print(f"  alpha={alpha:5.2f}  observed_false_alarm_rate={r['observed_false_alarm_rate']:.4f}  [{status}]")

    print()
    if all_ok:
        print("PASSED: observed false-alarm rate <= alpha (within simulation tolerance) at every "
              "tested alpha, confirming the conformal p-value's validity guarantee is correctly implemented.")
    else:
        print("FAILED: false-alarm rate exceeded alpha at some threshold — this means either the "
              "nonconformity computation or the p-value formula has a bug. Do NOT cite the "
              "false-alarm-rate guarantee until this passes.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
