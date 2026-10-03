"""
Inter-annotator agreement: Cohen's kappa (2 raters) and
Krippendorff's alpha (2+ raters, handles missing data).

## Accuracy caveat — please read

Cohen's kappa here is the standard, simple formula and its
correctness is easy to verify by hand (see test_annotator_agreement.py
for a worked example). Krippendorff's alpha is a genuinely more
complex statistic (coincidence-matrix-based, handles missing data
and multiple measurement levels) and implementations are known to be
easy to get subtly wrong. Before using the alpha implementation
here in an actual submission, CROSS-CHECK it against a reference
implementation (the `krippendorff` PyPI package, or R's `irr`
package) on your real annotation data. This implementation has only
been checked against a small hand-constructed example with perfect
and near-perfect agreement (see tests) — that is not sufficient
validation for a statistic this fiddly.
"""
from __future__ import annotations
from collections import Counter


def cohens_kappa(rater_a: list, rater_b: list) -> float:
    """Nominal-scale Cohen's kappa. rater_a/rater_b are equal-length lists of labels
    (same items, same order). Returns a value in roughly [-1, 1]; 1 = perfect agreement,
    0 = agreement no better than chance."""
    if len(rater_a) != len(rater_b):
        raise ValueError("rater_a and rater_b must be the same length")
    n = len(rater_a)
    if n == 0:
        return 0.0

    observed_agreement = sum(1 for a, b in zip(rater_a, rater_b) if a == b) / n

    labels = set(rater_a) | set(rater_b)
    count_a = Counter(rater_a)
    count_b = Counter(rater_b)
    expected_agreement = sum((count_a.get(l, 0) / n) * (count_b.get(l, 0) / n) for l in labels)

    if expected_agreement == 1.0:
        return 1.0  # avoid division by zero when both raters agree trivially on one label
    return round((observed_agreement - expected_agreement) / (1 - expected_agreement), 4)


def krippendorffs_alpha_nominal(reliability_data: list[list]) -> float:
    """
    `reliability_data` is one list per unit/item, containing the labels
    given by each rater who annotated that item — use None for a rater
    who didn't annotate a given item (Krippendorff's alpha natively
    handles missing data, which is its main advantage over kappa for
    real annotation projects with partial overlap).

    Nominal-scale only (categorical labels, no ordering assumed).
    See module docstring for the cross-validation caveat before trusting this.
    """
    # Build value-by-unit lists, dropping missing (None) entries.
    units = [[v for v in unit if v is not None] for unit in reliability_data]
    units = [u for u in units if len(u) >= 2]  # units with <2 ratings don't contribute
    if not units:
        return 1.0  # nothing to disagree on

    all_values = sorted({v for unit in units for v in unit})

    # Observed disagreement: sum over units of pairwise mismatches, weighted by unit size.
    def unit_disagreement(unit: list) -> float:
        m = len(unit)
        mismatches = sum(1 for i in range(m) for j in range(m) if i != j and unit[i] != unit[j])
        return mismatches / (m - 1) if m > 1 else 0.0

    total_pairs = sum(len(u) * (len(u) - 1) for u in units)
    if total_pairs == 0:
        return 1.0

    d_o = sum(len(u) * unit_disagreement(u) for u in units) / total_pairs

    # Expected disagreement: based on the overall distribution of values across all units.
    flat = [v for unit in units for v in unit]
    n_total = len(flat)
    value_counts = Counter(flat)
    d_e = 0.0
    for i, v1 in enumerate(all_values):
        for v2 in all_values:
            if v1 == v2:
                continue
            d_e += value_counts[v1] * value_counts[v2]
    d_e = d_e / (n_total * (n_total - 1)) if n_total > 1 else 1.0

    if d_e == 0:
        return 1.0
    return round(1 - (d_o / d_e), 4)
