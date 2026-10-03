"""
Attributable multivariate conformal drift scoring with Benjamini-Hochberg FDR.

The scalar conformal detector answers: "is this response unusual?"
This module additionally asks: "which persona dimensions provide statistically
unusual evidence?"

Each dimension has its own calibration text set.  A dimension-specific
nonconformity p-value is computed using the same leave-one-out kNN construction
as conformal.py.  Benjamini-Hochberg (BH) controls the expected false discovery
rate among the dimensions called anomalous at level q, under its standard
multiple-testing assumptions (or under positive dependence conditions for the
usual BH guarantee). The module reports raw p-values, adjusted q-values and
attributable dimensions separately; it does not collapse them into an opaque
single score.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.drift.conformal import _get_vector, _knn_nonconformity

MULTIVARIATE_CONFORMAL_VERSION = "spasm-multivariate-conformal-v1.0.0"


@dataclass(frozen=True)
class DimensionConformalResult:
    dimension: str
    p_value: float
    q_value: float
    rejected: bool
    nonconformity_score: float | None
    n_calibration: int
    backend: str | None
    status: str


def _bh_adjust(p_values: Mapping[str, float], q: float) -> dict[str, dict[str, float | bool]]:
    """Benjamini-Hochberg adjusted q-values and rejection decisions."""
    if not 0.0 < q < 1.0:
        raise ValueError("q must be in (0, 1)")
    ordered = sorted(p_values.items(), key=lambda kv: kv[1])
    m = len(ordered)
    q_values: dict[str, float] = {}
    running = 1.0
    for rank_from_end, (name, p) in enumerate(reversed(ordered), start=1):
        rank = m - rank_from_end + 1
        adjusted = min(1.0, p * m / rank)
        running = min(running, adjusted)
        q_values[name] = running

    # BH step-up rejection: largest rank with p_(i) <= i*q/m.
    cutoff_rank = 0
    for rank, (_, p) in enumerate(ordered, start=1):
        if p <= (rank * q / m):
            cutoff_rank = rank
    rejected_names = {name for rank, (name, _) in enumerate(ordered, start=1) if rank <= cutoff_rank}
    return {name: {"q_value": q_values[name], "rejected": name in rejected_names} for name in p_values}


def _dimension_p_value(response_text: str, calibration_texts: list[str], k: int) -> tuple[float, float, str] | None:
    if len(calibration_texts) < k + 1:
        return None
    vectors = []
    backend = None
    for text in calibration_texts:
        vector, used = _get_vector(text)
        vectors.append(vector)
        backend = used
    new_vector, new_backend = _get_vector(response_text)
    if new_backend != backend:
        raise RuntimeError("Embedding backend changed during multivariate conformal evaluation")

    null_scores = []
    for i, vector in enumerate(vectors):
        null_scores.append(_knn_nonconformity(vector, vectors[:i] + vectors[i + 1 :], k))
    new_score = _knn_nonconformity(new_vector, vectors, k)
    p = (1.0 + sum(s >= new_score for s in null_scores)) / (len(null_scores) + 1.0)
    return p, new_score, backend


def attributable_conformal_drift(
    response_text: str,
    dimension_calibration_texts: Mapping[str, list[str]],
    *,
    k: int = 3,
    fdr_q: float = 0.05,
) -> dict:
    """Return dimension-level conformal evidence plus BH-FDR attribution.

    Dimensions without enough calibration examples are returned as
    ``insufficient_calibration`` rather than being treated as non-drift.
    """
    raw: dict[str, float] = {}
    details: dict[str, dict] = {}
    for dimension, texts in dimension_calibration_texts.items():
        result = _dimension_p_value(response_text, texts, k)
        if result is None:
            details[dimension] = {
                "dimension": dimension,
                "status": "insufficient_calibration",
                "n_calibration": len(texts),
                "k": k,
                "p_value": None,
                "q_value": None,
                "rejected": False,
            }
            continue
        p, score, backend = result
        raw[dimension] = p
        details[dimension] = {
            "dimension": dimension,
            "status": "evaluated",
            "n_calibration": len(texts),
            "k": k,
            "p_value": round(p, 6),
            "nonconformity_score": round(score, 6),
            "backend": backend,
        }

    adjusted = _bh_adjust(raw, fdr_q) if raw else {}
    attributable = []
    for dimension, meta in details.items():
        if dimension in adjusted:
            meta.update({
                "q_value": round(float(adjusted[dimension]["q_value"]), 6),
                "rejected": bool(adjusted[dimension]["rejected"]),
            })
            if meta["rejected"]:
                attributable.append(dimension)

    return {
        "version": MULTIVARIATE_CONFORMAL_VERSION,
        "fdr_method": "benjamini_hochberg",
        "fdr_q": fdr_q,
        "dimensions": details,
        "attributable_dimensions": sorted(attributable),
        "n_tested_dimensions": len(raw),
        "n_rejected_dimensions": len(attributable),
        "global_attributable_drift": bool(attributable),
        "interpretation": (
            "At least one dimension has FDR-adjusted conformal evidence of drift."
            if attributable else
            "No evaluated dimension passed the BH-FDR threshold; insufficiently calibrated dimensions are not counted as negative evidence."
        ),
    }
