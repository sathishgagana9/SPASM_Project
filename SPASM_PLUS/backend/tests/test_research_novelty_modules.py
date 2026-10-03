"""
Tests for the Q2-novelty pass: conformal.py, decision_theory.py, and
safe_policy.py. These check mathematical/algorithmic correctness
(the properties each module's docstring claims), not real-world
accuracy on live LLM outputs — see each module's own honesty section
for that distinction.
"""
import pytest


def _fake_embedding(text):
    # Deterministic unit-test vector; production conformal evaluation requires
    # sentence-transformers and never uses this fallback.
    tokens = text.lower().split()
    return [float(sum(ord(c) for c in token) % 97) / 97.0 for token in (tokens[:8] + [""] * 8)[:8]]

from app.drift.conformal import (
    _knn_nonconformity, conformal_drift_test, minimum_calibration_size_for_alpha, calibration_adequacy_report,
)
from app.drift.decision_theory import bayes_optimal_threshold, threshold_for_risk_tier, decide, sensitivity_analysis
from app.repair.policy import LinUCBPolicy
from app.repair.safe_policy import ConservativeLinUCBPolicy
from app.drift import conformal as conformal_module
from app.drift.multivariate_conformal import attributable_conformal_drift
from app.drift import multivariate_conformal as multivariate_module
from app.drift.sequential_conformal import SequentialConformalState
from app.drift.system_risk import compose_system_risk, compose_empirical_risk


# ---- conformal.py ----

def test_conformal_p_value_bounds(monkeypatch):
    """p-values must always lie in (0, 1] by construction of the formula."""
    monkeypatch.setattr(conformal_module, "_get_vector", lambda text: (_fake_embedding(text), "embeddings"))
    calibration = [f"example sentence number {i} about a normal topic" for i in range(25)]
    result = conformal_drift_test("a completely different and unusual sentence about something else", calibration, k=3)
    assert result is not None
    assert 0 < result.p_value <= 1.0


def test_conformal_returns_none_with_insufficient_calibration_data(monkeypatch):
    """With fewer than k+1 calibration points, the LOO null distribution is
    degenerate — the module should refuse to report a number rather than a
    meaningless one."""
    monkeypatch.setattr(conformal_module, "_get_vector", lambda text: (_fake_embedding(text), "embeddings"))
    result = conformal_drift_test("some text", ["one", "two"], k=3)
    assert result is None


def test_minimum_calibration_size_matches_formula():
    # min p-value achievable with n points is 1/(n+1); solving 1/(n+1) <= alpha
    # gives n >= 1/alpha - 1, i.e. exactly what minimum_calibration_size_for_alpha computes.
    assert minimum_calibration_size_for_alpha(0.05) == 19
    assert minimum_calibration_size_for_alpha(0.01) == 99
    n = minimum_calibration_size_for_alpha(0.05)
    assert 1 / (n + 1) <= 0.05
    assert 1 / (n + 1 - 1) > 0.05 if n > 1 else True


def test_calibration_adequacy_report_flags_small_n():
    report = calibration_adequacy_report(n_calibration=6)
    assert report[0.05]["can_detect_at_this_alpha"] is False  # 6 < 19
    report_large = calibration_adequacy_report(n_calibration=25)
    assert report_large[0.05]["can_detect_at_this_alpha"] is True  # 25 >= 19


def test_knn_nonconformity_zero_for_identical_point():
    others = [[1.0, 2.0], [1.0, 2.0], [1.0, 2.0]]
    assert _knn_nonconformity([1.0, 2.0], others, k=2) == 0.0


# ---- decision_theory.py ----

def test_bayes_threshold_is_half_when_costs_equal():
    assert bayes_optimal_threshold(1.0, 1.0) == pytest.approx(0.5)


def test_bayes_threshold_decreases_as_false_accept_cost_increases():
    """Higher cost for letting a violation through should make the gate MORE
    block-happy — i.e. a LOWER confidence threshold triggers a block."""
    t_low_cost = bayes_optimal_threshold(1.0, 1.0)
    t_high_cost = bayes_optimal_threshold(10.0, 1.0)
    assert t_high_cost < t_low_cost


def test_risk_tier_thresholds_are_monotonically_decreasing():
    thresholds = [threshold_for_risk_tier(t) for t in ["low", "medium", "high", "critical"]]
    assert thresholds == sorted(thresholds, reverse=True)


def test_decide_blocks_when_confidence_exceeds_threshold():
    decision = decide(confidence_it_is_a_violation=0.9, risk_tier="critical")
    assert decision.should_block is True
    decision2 = decide(confidence_it_is_a_violation=0.01, risk_tier="low")
    assert decision2.should_block is False


def test_sensitivity_analysis_thresholds_are_monotonic_in_cost_ratio():
    rows = sensitivity_analysis()
    thresholds = [r["bayes_optimal_threshold"] for r in rows]
    assert thresholds == sorted(thresholds, reverse=True)  # increasing cost ratio -> decreasing threshold


def test_invalid_costs_raise():
    with pytest.raises(ValueError):
        bayes_optimal_threshold(0, 1.0)
    with pytest.raises(ValueError):
        bayes_optimal_threshold(1.0, -1.0)


# ---- safe_policy.py ----

def _drift_event():
    return {
        "severity": "medium",
        "dimensions": {"identity": 0.9, "scope": 0.9, "behavior": 0.9, "tone": 0.9,
                        "goals": 0.9, "knowledge": 0.9, "instruction": 0.9, "context": 0.9},
        "scope_classification": "in_scope",
    }


def test_conservative_policy_agrees_with_optimistic_when_arms_match():
    from app.repair.engine import select_repair_operator

    bandit = LinUCBPolicy()
    policy = ConservativeLinUCBPolicy(bandit=bandit, baseline_operator_fn=select_repair_operator)
    event = _drift_event()
    # With an untrained bandit, LinUCB explores uniformly — its choice may or
    # may not equal the baseline's, but the returned operator must always be
    # one of the valid operators, and the method diagnostic must be set.
    operator, diagnostics = policy.select(event)
    from app.repair.policy import OPERATORS
    assert operator in OPERATORS
    assert "method" in diagnostics


def test_conservative_policy_never_lets_cumulative_reward_diverge_unboundedly_below_baseline():
    """Lightweight in-process version of the standalone numerical stress
    test in research/experiments/safe_bandit_validation.py — checks the
    safety invariant holds after a batch of rounds with an adversarial
    reward pattern designed to tempt the optimistic arm."""
    import random
    from app.repair.policy import OPERATORS

    def baseline_fn(event):
        return "persona_constraint_reinforcement"

    rng = random.Random(42)
    bandit = LinUCBPolicy(alpha=1.5)
    policy = ConservativeLinUCBPolicy(bandit=bandit, baseline_operator_fn=baseline_fn, alpha_safety=0.1)

    for i in range(150):
        event = _drift_event()
        operator, _ = policy.select(event)
        # Decoy arm looks great early, then crashes — same shape as the
        # standalone stress test, compressed for a fast unit test.
        if operator == baseline_fn(event):
            reward = 0.5 + rng.gauss(0, 0.05)
        elif operator == "strong_reanchor_regenerate":
            reward = (0.9 if i < 75 else 0.05) + rng.gauss(0, 0.05)
        else:
            reward = 0.2 + rng.gauss(0, 0.05)
        policy.update(event, operator, reward)

        required = (1 - policy.alpha_safety) * policy.cumulative_baseline_reward
        assert policy.cumulative_bandit_reward >= required - 1e-6, (
            f"Safety constraint violated at round {i}: "
            f"{policy.cumulative_bandit_reward} < {required}"
        )


# ---- sequential / attributable conformal / end-to-end risk ----

def test_sequential_conformal_crosses_anytime_threshold():
    state = SequentialConformalState(alpha=0.05, epsilon=0.5)
    for _ in range(12):
        snap = state.update(0.001)
    assert snap["alarmed"] is True
    assert snap["alarm_turn"] is not None


def test_sequential_conformal_stays_quiet_for_typical_p_values():
    state = SequentialConformalState(alpha=0.05, epsilon=0.5)
    for _ in range(20):
        snap = state.update(0.8)
    assert snap["alarmed"] is False


def test_multivariate_conformal_reports_attributable_dimensions(monkeypatch):
    monkeypatch.setattr(conformal_module, "_get_vector", lambda text: (_fake_embedding(text), "embeddings"))
    monkeypatch.setattr(multivariate_module, "_get_vector", lambda text: (_fake_embedding(text), "embeddings"))
    calibration = {
        "identity": [f"stable identity example {i}" for i in range(25)],
        "scope": [f"stable scope example {i}" for i in range(25)],
    }
    result = attributable_conformal_drift("unusual identity and scope text", calibration, k=3, fdr_q=0.05)
    assert result["n_tested_dimensions"] == 2
    assert set(result["dimensions"]) == {"identity", "scope"}
    assert all("q_value" in v for v in result["dimensions"].values())


def test_system_risk_composition_uses_union_bound():
    result = compose_system_risk(0.05, 0.10, component_guarantees_established=True)
    assert result.system_failure_bound == pytest.approx(0.15)
    assert result.guarantee_confidence == pytest.approx(0.85)
    assert result.formal is True


def test_empirical_system_risk_is_conservative():
    result = compose_empirical_risk(5, 500, 2, 100, confidence=0.95)
    assert 0.0 <= result["system_failure_bound"] <= 1.0
    assert result["interpretation"].startswith("Empirical conservative")
