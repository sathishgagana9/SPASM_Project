"""
Head-to-head comparison report (Part A: "competitive positioning
against the closest prior art is what separates 'yet another
persona-drift system' from 'an advance over the state of the art'").

## What this does

Consumes already-produced `save_results()` JSON files from
baseline_vanilla.py, baseline_persona_prompt.py, baseline_detector.py,
and experiment_full_spasm.py, matches records by `(prompt_id,
model_label)` so comparisons are PAIRED (same prompt, same model,
different method — required for `paired_bootstrap_test`), and reports:

- mean final stability per method, with bootstrap CIs
- paired bootstrap significance test: full_spasm vs baseline_persona_prompt
  (the real ablation — "does drift-detection + repair add anything
  beyond the system prompt alone?")
- repair-specific metrics (success rate, mean cycles_used, mean
  stability_improvement) for full_spasm only, since baselines don't repair

## What this does NOT do (read before citing "we beat prior work")

This does NOT include a row for Nautilus Compass or Li et al. (2024)'s
reminder-based mitigation with real numbers — replicating either
requires their published code/prompts, which this environment has no
network access to fetch and which were never provided as part of this
project's inputs. `PRIOR_WORK_PLACEHOLDER` rows are included in the
output so the table's shape is ready — fill in real numbers by:
  1. running their public implementation (if released) against the
     SAME benchmark and models used here, or
  2. reimplementing their described method as a new experiment script
     in this directory (mirroring baseline_persona_prompt.py's
     structure) if no code is released, clearly noted as a
     reimplementation with any deviations from the paper's description.
Do NOT report the placeholder numbers as real — they are None on
purpose. A reviewer checking your related-work comparison table
against this script's output would immediately see fabricated numbers
as a red flag; leaving them None until you've actually run the
comparison is the honest choice.

Usage:
    python comparison_report.py \\
        --vanilla "../results/raw/baseline_vanilla_*.json" \\
        --persona-prompt "../results/raw/baseline_persona_prompt_*.json" \\
        --full-spasm "../results/raw/experiment_full_spasm_lookup_*.json"
"""
import argparse
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from evaluation.statistical_tests import bootstrap_ci, describe, paired_bootstrap_test  # noqa: E402

RESULTS_PATH = Path(__file__).parent.parent / "results" / "tables" / "comparison_report.json"

PRIOR_WORK_PLACEHOLDER = {
    "Nautilus Compass": {"status": "not_replicated", "reason": "no released code/prompts available in this environment"},
    "Li et al. (2024) reminder-based mitigation": {"status": "not_replicated", "reason": "no released code/prompts available in this environment"},
}


def load_records(pattern: str) -> list[dict]:
    records = []
    for path in glob.glob(pattern):
        with open(path) as f:
            payload = json.load(f)
        records.extend(payload.get("records", []))
    return records


def _stability(record: dict) -> float | None:
    """Extracts a comparable 'final stability' number from records of
    ANY of the four experiment scripts' differing schemas."""
    if "final_stability" in record:
        return record["final_stability"]
    if "drift_result" in record and record["drift_result"]:
        return record["drift_result"].get("overall_stability")
    return None


def _key(record: dict) -> tuple:
    return (record.get("prompt_id"), record.get("model_label"))


def compare(vanilla_pattern: str | None, persona_prompt_pattern: str, full_spasm_pattern: str) -> dict:
    persona_prompt_records = load_records(persona_prompt_pattern)
    full_spasm_records = load_records(full_spasm_pattern)

    if not persona_prompt_records or not full_spasm_records:
        raise SystemExit(
            "Need both --persona-prompt and --full-spasm results to run the core ablation comparison. "
            "Run baseline_persona_prompt.py and experiment_full_spasm.py first — see EXPERIMENTS.md."
        )

    report: dict = {"methods": {}, "prior_work": PRIOR_WORK_PLACEHOLDER}

    for label, records in [("baseline_persona_prompt", persona_prompt_records), ("experiment_full_spasm", full_spasm_records)]:
        stabilities = [_stability(r) for r in records if _stability(r) is not None]
        report["methods"][label] = {
            "n": len(stabilities),
            "stability": describe(stabilities),
            "stability_ci": bootstrap_ci(stabilities) if len(stabilities) >= 2 else None,
        }

    if vanilla_pattern:
        vanilla_records = load_records(vanilla_pattern)
        report["methods"]["baseline_vanilla"] = {
            "n": len(vanilla_records),
            "note": "Vanilla has no persona system prompt, so no comparable drift-detector stability score exists "
                    "for it by construction — report this row's raw response content / qualitative comparison "
                    "separately, not a stability number that would misleadingly imply it was scored the same way.",
        }

    # Paired ablation: full_spasm vs baseline_persona_prompt, matched by (prompt_id, model_label)
    pp_by_key = {_key(r): _stability(r) for r in persona_prompt_records if _stability(r) is not None}
    fs_by_key = {_key(r): _stability(r) for r in full_spasm_records if _stability(r) is not None}
    shared_keys = sorted(set(pp_by_key) & set(fs_by_key))

    if len(shared_keys) < 2:
        report["ablation_full_spasm_vs_persona_prompt"] = {
            "status": "insufficient_paired_data",
            "n_shared_keys": len(shared_keys),
            "note": "Need matching (prompt_id, model_label) records in both result sets — make sure both "
                    "experiments were run over the SAME dataset/config.",
        }
    else:
        a = [fs_by_key[k] for k in shared_keys]
        b = [pp_by_key[k] for k in shared_keys]
        report["ablation_full_spasm_vs_persona_prompt"] = {
            "n_paired": len(shared_keys),
            "full_spasm_mean": describe(a)["mean"],
            "persona_prompt_mean": describe(b)["mean"],
            **paired_bootstrap_test(a, b),
            "interpretation": "mean_diff = full_spasm - persona_prompt. p_value < 0.05 conventionally taken as "
                               "evidence the difference isn't due to chance — report the CI alongside it, not just "
                               "the p-value (spec/statistical hygiene: effect size and CI, not point estimates alone).",
        }

    # Repair-specific metrics, full_spasm only
    repaired = [r for r in full_spasm_records if r.get("repair_result")]
    if repaired:
        successes = [r["repair_result"]["success"] for r in repaired]
        improvements = [r["repair_result"]["stability_improvement"] for r in repaired]
        cycles = [r["repair_result"].get("cycles_used") for r in repaired if r["repair_result"].get("cycles_used") is not None]
        report["repair_analysis"] = {
            "n_drift_events_repaired": len(repaired),
            "success_rate": round(sum(successes) / len(successes), 4),
            "stability_improvement": describe(improvements),
            "cycles_used": describe(cycles) if cycles else None,
        }
    else:
        report["repair_analysis"] = {"n_drift_events_repaired": 0, "note": "No drift was detected/repaired in this run."}

    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vanilla", type=str, default=None)
    parser.add_argument("--persona-prompt", type=str, required=True)
    parser.add_argument("--full-spasm", type=str, required=True)
    args = parser.parse_args()

    report = compare(args.vanilla, args.persona_prompt, args.full_spasm)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    print(f"\nFull report written to {RESULTS_PATH}")
    print("\nPrior-work rows are placeholders (status='not_replicated') — see this script's module docstring "
          "for what's needed before those can carry real numbers in a paper.")


if __name__ == "__main__":
    main()
