"""Correctness tests for Cohen's kappa and Krippendorff's alpha."""
from research.evaluation.annotator_agreement import cohens_kappa, krippendorffs_alpha_nominal


def test_cohens_kappa_perfect_agreement():
    a = ["compliant", "violation", "compliant", "violation"]
    b = ["compliant", "violation", "compliant", "violation"]
    assert cohens_kappa(a, b) == 1.0


def test_cohens_kappa_chance_agreement_is_near_zero():
    # Constructed so observed agreement roughly equals expected (chance) agreement.
    a = ["x", "x", "y", "y"]
    b = ["x", "y", "x", "y"]
    kappa = cohens_kappa(a, b)
    assert -0.2 <= kappa <= 0.2


def test_cohens_kappa_hand_computed_example():
    # 10 items, 8 agreements on a 2-class label -> observed = 0.8
    a = ["yes"] * 6 + ["no"] * 4
    b = ["yes"] * 5 + ["no"] * 1 + ["no"] * 4  # 1 disagreement (item 6: a=yes, b=no)
    observed = sum(1 for x, y in zip(a, b) if x == y) / 10
    assert observed == 0.9
    kappa = cohens_kappa(a, b)
    assert 0.0 < kappa < 1.0  # some agreement, not perfect, not zero


def test_krippendorff_perfect_agreement():
    data = [["a", "a", "a"], ["b", "b", "b"], ["a", "a", "a"]]
    assert krippendorffs_alpha_nominal(data) == 1.0


def test_krippendorff_handles_missing_data():
    # Some units have only 2 of 3 raters — should not error, should still compute.
    data = [["a", "a", None], ["b", None, "b"], ["a", "b", "a"]]
    result = krippendorffs_alpha_nominal(data)
    assert isinstance(result, float)


def test_krippendorff_total_disagreement_is_low():
    data = [["a", "b"], ["b", "a"], ["a", "b"], ["b", "a"]]
    result = krippendorffs_alpha_nominal(data)
    assert result < 0.3  # raters systematically disagree
