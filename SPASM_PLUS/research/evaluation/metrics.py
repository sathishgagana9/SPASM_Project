"""
Detection metrics: accuracy, precision, recall, F1, AUROC, AUPRC.

Pure stdlib, no dependencies — runs anywhere without installing
numpy/sklearn. For a real paper submission, cross-check these
against sklearn.metrics on the same data as a sanity check; these
are provided so the pipeline doesn't require a heavy dependency for
sanity checking during development.

All functions take `labels: list[bool]` (ground truth: True = drift
occurred) and either `predictions: list[bool]` (binary decision) or
`scores: list[float]` (continuous score, higher = more likely drift)
depending on the metric.
"""
from __future__ import annotations


def _confusion_counts(predictions: list[bool], labels: list[bool]) -> tuple[int, int, int, int]:
    if len(predictions) != len(labels):
        raise ValueError("predictions and labels must be the same length")
    tp = sum(1 for p, y in zip(predictions, labels) if p and y)
    fp = sum(1 for p, y in zip(predictions, labels) if p and not y)
    tn = sum(1 for p, y in zip(predictions, labels) if not p and not y)
    fn = sum(1 for p, y in zip(predictions, labels) if not p and y)
    return tp, fp, tn, fn


def accuracy(predictions: list[bool], labels: list[bool]) -> float:
    tp, fp, tn, fn = _confusion_counts(predictions, labels)
    total = tp + fp + tn + fn
    return (tp + tn) / total if total else 0.0


def precision(predictions: list[bool], labels: list[bool]) -> float:
    tp, fp, _, _ = _confusion_counts(predictions, labels)
    return tp / (tp + fp) if (tp + fp) else 0.0


def recall(predictions: list[bool], labels: list[bool]) -> float:
    tp, _, _, fn = _confusion_counts(predictions, labels)
    return tp / (tp + fn) if (tp + fn) else 0.0


def f1_score(predictions: list[bool], labels: list[bool]) -> float:
    p, r = precision(predictions, labels), recall(predictions, labels)
    return 2 * p * r / (p + r) if (p + r) else 0.0


def auroc(scores: list[float], labels: list[bool]) -> float | None:
    """Returns tie-correct AUROC; None if labels are all one class.

    Uses the rank-sum/Mann-Whitney formulation with average ranks for tied
    scores, matching the standard AUROC convention and sklearn behavior.
    """
    if len(scores) != len(labels):
        raise ValueError("scores and labels must be the same length")
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return None

    ranked = sorted(zip(scores, labels), key=lambda x: x[0])
    sum_positive_ranks = 0.0
    i = 0
    rank = 1
    while i < len(ranked):
        j = i + 1
        while j < len(ranked) and ranked[j][0] == ranked[i][0]:
            j += 1
        avg_rank = (rank + (rank + (j - i) - 1)) / 2.0
        sum_positive_ranks += avg_rank * sum(1 for _, label in ranked[i:j] if label)
        rank += j - i
        i = j

    auc = (sum_positive_ranks - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return round(auc, 4)


def auprc(scores: list[float], labels: list[bool]) -> float | None:
    n_pos = sum(labels)
    if n_pos == 0:
        return None
    pairs = sorted(zip(scores, labels), key=lambda x: -x[0])
    tp = fp = 0
    points = []
    for score, label in pairs:
        if label:
            tp += 1
        else:
            fp += 1
        prec = tp / (tp + fp) if (tp + fp) else 1.0
        rec = tp / n_pos
        points.append((rec, prec))
    points = sorted(set(points))
    auc = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        auc += (x1 - x0) * (y0 + y1) / 2
    return round(auc, 4)


def dimension_adherence_means(dimension_scores: list[dict[str, float]]) -> dict[str, float]:
    """Given a list of per-example dimension-score dicts, returns the mean per dimension.
    This is a descriptive summary, not a validated "adherence accuracy" metric."""
    if not dimension_scores:
        return {}
    all_dims = {d for entry in dimension_scores for d in entry}
    return {
        d: round(sum(entry.get(d, 0.0) for entry in dimension_scores) / len(dimension_scores), 4)
        for d in all_dims
    }
