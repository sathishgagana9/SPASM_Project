"""Correctness tests for bootstrap CI and paired bootstrap significance testing."""
from research.evaluation.statistical_tests import describe, bootstrap_ci, paired_bootstrap_test


def test_describe_basic():
    result = describe([1, 2, 3, 4, 5])
    assert result["mean"] == 3.0
    assert result["median"] == 3.0
    assert result["n"] == 5


def test_bootstrap_ci_contains_true_mean_for_constant_data():
    data = [5.0] * 20
    result = bootstrap_ci(data)
    assert result["point_estimate"] == 5.0
    assert result["ci_low"] == 5.0
    assert result["ci_high"] == 5.0


def test_bootstrap_ci_is_reproducible_with_fixed_seed():
    data = [1, 2, 3, 4, 5, 6, 7, 8, 2, 3, 4, 5]
    r1 = bootstrap_ci(data, seed=42)
    r2 = bootstrap_ci(data, seed=42)
    assert r1 == r2


def test_paired_bootstrap_detects_clear_difference():
    a = [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]  # method A consistently better
    b = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    result = paired_bootstrap_test(a, b)
    assert result["mean_diff"] > 0
    assert result["p_value"] < 0.05


def test_paired_bootstrap_no_difference_when_identical():
    a = [0.7, 0.6, 0.8, 0.5, 0.9]
    b = [0.7, 0.6, 0.8, 0.5, 0.9]
    result = paired_bootstrap_test(a, b)
    assert result["mean_diff"] == 0.0
    assert result["p_value"] == 1.0
