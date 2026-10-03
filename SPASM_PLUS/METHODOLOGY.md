# Methodology

## Experimental protocol (once you run this for real)

1. **Fix the model/config matrix first.** Edit `research/experiments/config.yaml` —
   decide which models (small local / stronger local / cloud) you're testing before running anything.
2. **Run all four baseline conditions on the same prompt set** (`baseline_vanilla.py`
   → `baseline_persona_prompt.py` → `baseline_detector.py` → `experiment_full_spasm.py`)
   so comparisons are paired (same prompts, same model, same temperature) — required for
   `research/evaluation/statistical_tests.py::paired_bootstrap_test` to be valid.
3. **Do not tune detection thresholds on the same data you evaluate on.** Split
   SPASM-DriftBench into dev/test before touching thresholds. Use
   `calibration.py::select_threshold_from_dev_set` on dev only, then report the
   chosen threshold's performance on test.
4. **Get real annotations before reporting any accuracy number.** The synthetic
   labels in the dataset are for development, not for reporting in a paper — see
   BENCHMARK.md.
5. **Report calibration, not just accuracy.** `drift_probability` is uncalibrated
   by construction until you run `calibration.py` against labeled outcomes — report
   Brier score / ECE alongside any probability-based claim.
6. **Use paired statistical tests for baseline comparisons** (same prompts across
   conditions) rather than unpaired tests — `statistical_tests.py::paired_bootstrap_test`
   does this without requiring scipy, though cross-checking against scipy's paired
   t-test or Wilcoxon signed-rank is recommended before submission.

## Threats to validity (be upfront about these in any writeup)

- **Detector construct validity**: the scope/context dimensions are lexical-overlap
  heuristics, not semantic understanding — see `RESEARCH.md`'s honesty table. Any
  claimed "the detector understands X" needs a validity argument, not an assumption.
- **Dataset size**: 22 core prompts is not enough for confident per-persona metrics.
  Confidence intervals from `bootstrap_ci` will be wide at this scale — report them,
  don't hide them.
- **Single-annotator risk**: until real multi-annotator data exists, any
  "ground truth" is really one perspective (the dataset author's).
- **Model-specific findings**: results from one small local model don't establish
  "SPASM++ works independently of the underlying LLM" — that claim needs the
  cross-model experiment actually run (§16), not assumed from architecture alone.
- **Prompt-injection ceiling**: the current mitigation is prompt-level instruction
  only; a sufficiently adversarial prompt can likely still break it. Report the
  adversarial experiment's failure rate honestly, including cases where it fails.

## Reproducibility requirements this repo tries to satisfy

- Every experiment result includes `detector_version` and `threshold_version`
  (`backend/app/drift/scoring.py`) so results can be tied to the exact logic that produced them.
- Every experiment script writes its full config alongside results (`common.py::save_results`).
- Bootstrap procedures use a fixed default seed (`statistical_tests.py`) so re-running
  produces identical CIs/p-values unless you explicitly ask for a fresh resample.

## SPASM++ temporal and attributable conformal extension

The current research implementation adds three layers beyond one-shot
conformal detection:

1. **Sequential evidence:** `SequentialConformalState` accumulates per-turn
   conformal p-values through a nonnegative power-betting test martingale. The
   anytime interpretation requires conditional super-uniform p-values under
the null; the implementation does not assume that ordinary exchangeability
   alone is enough for arbitrary dependent conversations.
2. **Attribution:** `attributable_conformal_drift()` computes one p-value per
   persona dimension and applies Benjamini-Hochberg FDR correction. Dimensions
   with insufficient calibration are marked as unevaluated, not treated as
   evidence of stability.
3. **System risk:** `compose_system_risk()` and `compose_empirical_risk()` keep
   detector false alarms and repair safety failures as separate components and
   combine them conservatively with a union bound. The empirical variant uses
   one-sided Clopper-Pearson upper confidence bounds and must be reported as an
   empirical held-out bound, not as a distribution-free guarantee.

### Calibration discipline

Calibration, development, and test data must remain disjoint. Thresholds,
FDR levels, betting parameters, and repair-policy hyperparameters must be
frozen using development data before the final test run. Real embedding
experiments must set `SPASM_SEMANTIC_BACKEND=embeddings`; the conformal path
contains no silent hashed-vector fallback.
