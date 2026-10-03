"""Correctness tests for research/evaluation/calibration.py."""
from research.evaluation.calibration import brier_score, expected_calibration_error, select_threshold_from_dev_set


def test_brier_score_perfect_predictions():
    assert brier_score([1.0, 0.0, 1.0], [True, False, True]) == 0.0


def test_brier_score_worst_case():
    # predicting 1.0 when label is False (and vice versa) -> squared error 1.0 each
    assert brier_score([1.0, 0.0], [False, True]) == 1.0


def test_ece_perfect_calibration():
    # predicted probability exactly matches empirical frequency in each bin
    probs = [0.1] * 10  # 10 examples all predicted 0.1
    labels = [True] * 1 + [False] * 9  # empirical rate = 0.1, matches prediction
    ece = expected_calibration_error(probs, labels, n_bins=10)
    assert ece < 0.05  # should be close to 0, allowing for bin-boundary rounding


def test_threshold_selection_does_not_touch_test_data():
    # Only dev data is passed in — function signature makes it impossible to leak test data.
    dev_scores = [0.1, 0.4, 0.6, 0.9]
    dev_labels = [False, False, True, True]
    result = select_threshold_from_dev_set(dev_scores, dev_labels, metric="f1")
    assert result["n_dev_examples"] == 4
    assert 0.0 <= result["dev_value"] <= 1.0
