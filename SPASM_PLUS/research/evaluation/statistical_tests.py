"""
Statistical utilities: descriptive stats, bootstrap confidence
intervals, and paired bootstrap significance testing.

Deliberately dependency-free (stdlib `statistics` + `random` only)
so this runs without installing scipy. Bootstrap resampling is used
for both CIs and significance testing because it makes no
distributional assumptions (no normality assumption needed, unlike a
paired t-test) — appropriate given these are typically small,
non-normal samples (a handful of experiment conditions x prompts).

For a real submission, ALSO run the equivalent scipy/statsmodels
test (paired t-test or Wilcoxon signed-rank) as a cross-check —
these are provided as an accessible, install-free first pass, not a
replacement for a properly reviewed statistical pipeline.
"""
from __future__ import annotations
import random
import statistics as _stats


def describe(data: list[float]) -> dict:
    if not data:
        return {"mean": None, "stdev": None, "median": None, "n": 0}
    return {
        "mean": round(_stats.mean(data), 4),
        "stdev": round(_stats.stdev(data), 4) if len(data) > 1 else 0.0,
        "median": round(_stats.median(data), 4),
        "n": len(data),
    }


def bootstrap_ci(data: list[float], statistic=_stats.mean, n_resamples: int = 2000, ci: float = 0.95, seed: int | None = 42) -> dict:
    """Percentile bootstrap CI for an arbitrary statistic (default: mean).
    `seed` defaults to a fixed value so results are reproducible run-to-run —
    pass None for a non-deterministic resample."""
    if len(data) < 2:
        return {"point_estimate": data[0] if data else None, "ci_low": None, "ci_high": None, "n_resamples": 0}

    rng = random.Random(seed)
    point_estimate = statistic(data)
    resample_stats = []
    n = len(data)
    for _ in range(n_resamples):
        resample = [data[rng.randrange(n)] for _ in range(n)]
        resample_stats.append(statistic(resample))
    resample_stats.sort()

    alpha = 1 - ci
    lo_idx = int((alpha / 2) * n_resamples)
    hi_idx = int((1 - alpha / 2) * n_resamples) - 1
    return {
        "point_estimate": round(point_estimate, 4),
        "ci_low": round(resample_stats[lo_idx], 4),
        "ci_high": round(resample_stats[hi_idx], 4),
        "ci_level": ci,
        "n_resamples": n_resamples,
    }


def paired_bootstrap_test(a: list[float], b: list[float], n_resamples: int = 2000, seed: int | None = 42) -> dict:
    """
    Paired comparison: a and b must be the same length, same order
    (e.g. the same prompts evaluated under method A vs method B).
    Tests whether mean(a) - mean(b) is significantly different from
    zero by bootstrapping the paired differences. Returns a two-sided
    p-value estimate (proportion of bootstrap resamples where the
    sign of the mean difference flips relative to the observed sign).
    """
    if len(a) != len(b):
        raise ValueError("a and b must be the same length (paired observations)")
    if len(a) < 2:
        return {"mean_diff": None, "p_value": None, "n": len(a)}

    diffs = [x - y for x, y in zip(a, b)]
    observed_mean_diff = _stats.mean(diffs)

    rng = random.Random(seed)
    n = len(diffs)
    resample_means = []
    for _ in range(n_resamples):
        resample = [diffs[rng.randrange(n)] for _ in range(n)]
        resample_means.append(_stats.mean(resample))

    if observed_mean_diff >= 0:
        p_value = sum(1 for m in resample_means if m <= 0) / n_resamples
    else:
        p_value = sum(1 for m in resample_means if m >= 0) / n_resamples
    p_value = min(1.0, 2 * p_value)  # two-sided

    return {
        "mean_diff": round(observed_mean_diff, 4),
        "p_value": round(p_value, 4),
        "n": n,
        "n_resamples": n_resamples,
        "method": "paired_bootstrap",
    }
