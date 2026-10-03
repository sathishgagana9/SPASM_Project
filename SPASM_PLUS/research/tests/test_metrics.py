"""Correctness tests for research/evaluation/metrics.py against hand-computed values."""
from research.evaluation.metrics import accuracy, precision, recall, f1_score, auroc, auprc, dimension_adherence_means


def test_perfect_predictions():
    preds = [True, True, False, False]
    labels = [True, True, False, False]
    assert accuracy(preds, labels) == 1.0
    assert precision(preds, labels) == 1.0
    assert recall(preds, labels) == 1.0
    assert f1_score(preds, labels) == 1.0


def test_known_confusion_matrix():
    # tp=2, fp=1, tn=2, fn=1 (hand-verified)
    preds  = [True, True, True, False, False, False]
    labels = [True, True, False, False, False, True]
    assert accuracy(preds, labels) == 4 / 6
    assert precision(preds, labels) == 2 / 3
    assert recall(preds, labels) == 2 / 3
    expected_f1 = 2 * (2/3) * (2/3) / ((2/3) + (2/3))
    assert abs(f1_score(preds, labels) - expected_f1) < 1e-9


def test_auroc_perfect_separation():
    scores = [0.9, 0.8, 0.2, 0.1]
    labels = [True, True, False, False]
    assert auroc(scores, labels) == 1.0


def test_auroc_random_separation_is_near_half():
    # Scores don't correlate with labels at all -> AUROC near 0.5
    scores = [0.5, 0.5, 0.5, 0.5]
    labels = [True, False, True, False]
    result = auroc(scores, labels)
    assert result is not None
    assert 0.4 <= result <= 0.6


def test_auroc_undefined_when_single_class():
    assert auroc([0.1, 0.9], [True, True]) is None


def test_dimension_adherence_means():
    data = [{"scope": 1.0, "tone": 0.5}, {"scope": 0.0, "tone": 1.0}]
    means = dimension_adherence_means(data)
    assert means["scope"] == 0.5
    assert means["tone"] == 0.75
