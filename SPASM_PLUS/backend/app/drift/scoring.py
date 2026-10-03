"""
Formal drift scoring (spec sections 8-9).

PS(r, P, H) = Σ w_d · S_d(r, P, H)   over d in DIMENSIONS

This module deliberately separates three distinct numbers that were
previously conflated:

- drift_score:       1 - PS(r,P,H). Bounded [0,1]. Deterministic
                      given the dimension scores and weights.
- drift_probability: a monotonic transform of drift_score intended
                      to look like a probability. It is NOT a
                      calibrated probability — no labeled dataset has
                      been used to fit it. Calling it "probability of
                      drift" without this caveat overstates what it
                      is. See research/evaluation/calibration.py for
                      how to actually calibrate this once labeled
                      data exists.
- confidence:        how far the overall stability score sits from
                      the nearest severity-threshold boundary,
                      normalized to [0,1]. This is a common heuristic
                      for "how firmly does this fall in its bucket",
                      not a statistical confidence interval.

DETECTOR_VERSION / THRESHOLD_VERSION are stamped onto every
DriftEvent so experiment results can be tied to the exact detector
logic and threshold configuration that produced them (spec section
25 — provenance for reproducibility).
"""
from app.core.config import get_settings

DETECTOR_VERSION = "raise-drift-v2.0.0"
THRESHOLD_VERSION = "manual-v1"  # PROVISIONAL — not calibrated; bump this if thresholds change

DIMENSIONS = ["identity", "scope", "behavior", "tone", "goals", "knowledge", "instruction", "context"]

# Equal weighting by default — PROVISIONAL, not validated. Override via weights= param.
DEFAULT_WEIGHTS = {d: 1.0 / len(DIMENSIONS) for d in DIMENSIONS}


def compute_stability(dimension_scores: dict[str, float], weights: dict[str, float] | None = None) -> float:
    w = weights or DEFAULT_WEIGHTS
    total_weight = sum(w.get(d, 0.0) for d in dimension_scores)
    if total_weight == 0:
        return sum(dimension_scores.values()) / max(len(dimension_scores), 1)
    return sum(dimension_scores[d] * w.get(d, 0.0) for d in dimension_scores) / total_weight


def classify_severity(overall_stability: float) -> str:
    settings = get_settings()
    if overall_stability >= settings.drift_severity_low_threshold:
        return "low"
    if overall_stability >= settings.drift_severity_medium_threshold:
        return "medium"
    if overall_stability >= settings.drift_severity_high_threshold:
        return "high"
    return "critical"


def compute_confidence(overall_stability: float) -> float:
    """Distance from the nearest severity-threshold boundary, normalized.
    Heuristic, not a statistical confidence interval — see module docstring."""
    settings = get_settings()
    boundaries = [
        settings.drift_severity_high_threshold,
        settings.drift_severity_medium_threshold,
        settings.drift_severity_low_threshold,
    ]
    nearest_dist = min(abs(overall_stability - b) for b in boundaries)
    # Normalize against half the smallest gap between adjacent thresholds so values stay in a sane range.
    gaps = [
        settings.drift_severity_low_threshold - settings.drift_severity_medium_threshold,
        settings.drift_severity_medium_threshold - settings.drift_severity_high_threshold,
    ]
    scale = max(min(g for g in gaps if g > 0) / 2, 1e-6) if any(g > 0 for g in gaps) else 0.1
    return round(min(1.0, nearest_dist / scale), 2)


def compute_drift_probability(drift_score: float) -> float:
    """Monotonic transform of drift_score. NOT calibrated — see module docstring."""
    return round(min(1.0, max(0.0, drift_score)), 4)
