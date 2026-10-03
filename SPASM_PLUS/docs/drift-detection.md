# Drift Detection (Phase 4/5)

## Current implementation: rule-based, NOT a trained classifier

`backend/app/drift/detector.py` computes 7 dimension scores
(identity, behavior, tone, goals, knowledge, instruction, context)
from deterministic string/keyword checks against the persona config
and the actual response text. Nothing here is randomized or
fabricated — every score is a real function of real inputs — but the
*scoring logic* is a first-pass heuristic, not a validated model.

## Formula (PROVISIONAL)

Each dimension starts at 1.0 and is penalized for specific rule
violations (forbidden-phrase matches, casualness heuristics for
tone, generic AI disclaimers for identity, etc. — full breakdown in
the detector's docstring). `overall_stability` is the unweighted
mean of all 7 dimensions. Severity thresholds are configurable via
`DRIFT_SEVERITY_*_THRESHOLD` env vars, not hard-coded in the
frontend.

## Known limitations

- **context** dimension is fixed at 1.0 — true context-drift
  detection needs multi-turn comparison against conversation
  history, which is NOT IMPLEMENTED.
- **goals** dimension uses weak keyword overlap, not semantic
  understanding — a response can satisfy a goal without containing
  any of its keywords, and vice versa.
- Weighting across dimensions is unweighted/equal — no evidence this
  is the right weighting. PROVISIONAL.
- This has not been evaluated against any labeled drift dataset. No
  precision/recall/F1 numbers exist for it. Until StressBench +
  evaluation harness (Phases 11/12) actually run, any such number
  would be fabricated — so none appear anywhere in this repo.

## Path to a real classifier

The detector's return shape (`dimensions`, `drift_type`, `severity`,
`confidence`, `reason`, `method`) is the contract the rest of the
system depends on. A trained classifier or an LLM-as-judge
implementation can replace `detect_drift()` as a drop-in as long as
it returns the same shape — `method` should change from
`"rule_based"` to `"llm_assisted"` or `"trained_classifier"`
accordingly so the UI's "Technical details" panel stays honest.
