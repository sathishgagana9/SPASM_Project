"""
Calibration utilities: Brier score, Expected Calibration Error (ECE),
reliability-diagram data, and dev-set threshold selection.

Use these to actually calibrate the detector's drift_probability
(currently an uncalibrated heuristic — see backend/app/drift/scoring.py)
once you have labeled data. Threshold selection here is explicitly
meant to run on a DEV split, never the test split — the function
signature takes dev_scores/dev_labels to make that split unambiguous
at the call site.
"""
from __future__ import annotations


def brier_score(probabilities: list[float], labels: list[bool]) -> float:
    """Lower is better. 0 = perfect, 0.25 = no better than always predicting 0.5."""
    if len(probabilities) != len(labels):
        raise ValueError("probabilities and labels must be the same length")
    if not probabilities:
        return 0.0
    return round(sum((p - float(y)) ** 2 for p, y in zip(probabilities, labels)) / len(probabilities), 4)


def expected_calibration_error(probabilities: list[float], labels: list[bool], n_bins: int = 10) -> float:
    """Standard ECE: bin predictions by confidence, compare mean predicted
    probability to actual positive rate in each bin, weight by bin size."""
    if not probabilities:
        return 0.0
    bins = [[] for _ in range(n_bins)]
    for p, y in zip(probabilities, labels):
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, y))

    n = len(probabilities)
    ece = 0.0
    for bin_items in bins:
        if not bin_items:
            continue
        bin_conf = sum(p for p, _ in bin_items) / len(bin_items)
        bin_acc = sum(1 for _, y in bin_items if y) / len(bin_items)
        ece += (len(bin_items) / n) * abs(bin_conf - bin_acc)
    return round(ece, 4)


def reliability_diagram_data(probabilities: list[float], labels: list[bool], n_bins: int = 10) -> list[dict]:
    """Returns per-bin (mean_confidence, empirical_accuracy, count) for plotting a reliability diagram."""
    bins = [[] for _ in range(n_bins)]
    for p, y in zip(probabilities, labels):
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, y))

    result = []
    for i, bin_items in enumerate(bins):
        lo, hi = i / n_bins, (i + 1) / n_bins
        if not bin_items:
            result.append({"bin_range": [lo, hi], "mean_confidence": None, "empirical_accuracy": None, "count": 0})
            continue
        mean_conf = sum(p for p, _ in bin_items) / len(bin_items)
        acc = sum(1 for _, y in bin_items if y) / len(bin_items)
        result.append({"bin_range": [lo, hi], "mean_confidence": round(mean_conf, 4), "empirical_accuracy": round(acc, 4), "count": len(bin_items)})
    return result


def select_threshold_from_dev_set(dev_scores: list[float], dev_labels: list[bool], metric: str = "f1") -> dict:
    """
    Sweeps candidate thresholds over the DEV set only and returns the
    threshold maximizing the requested metric, plus that metric's dev-set
    value. Caller is responsible for evaluating the chosen threshold on a
    SEPARATE test/held-out set — this function never sees test data,
    by design, so it cannot leak into the reported result (spec section 8:
    "do not tune final thresholds on the test set").
    """
    from research.evaluation.metrics import f1_score, precision, recall, accuracy

    metric_fns = {"f1": f1_score, "precision": precision, "recall": recall, "accuracy": accuracy}
    if metric not in metric_fns:
        raise ValueError(f"Unknown metric '{metric}', choose from {list(metric_fns)}")
    metric_fn = metric_fns[metric]

    candidates = sorted(set(dev_scores))
    best_threshold, best_value = 0.5, -1.0
    for t in candidates:
        preds = [s >= t for s in dev_scores]
        value = metric_fn(preds, dev_labels)
        if value > best_value:
            best_value, best_threshold = value, t

    return {"threshold": best_threshold, "dev_metric": metric, "dev_value": round(best_value, 4), "n_dev_examples": len(dev_scores)}
