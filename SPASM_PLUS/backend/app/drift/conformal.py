"""
Conformal anomaly detection for persona-response drift.

## The gap this fills

Every existing drift/scope signal in this codebase (and, per the
literature survey in RESEARCH_CONTRIBUTION.md, every closely related
system we could find — Nautilus Compass's cosine-similarity threshold,
this project's own lexical/embedding scope-similarity threshold) makes
an accept/reject decision by comparing a similarity SCORE against a
HAND-PICKED THRESHOLD (e.g. `OUT_OF_SCOPE_THRESHOLD = 0.06`). That
threshold has no statistical meaning attached to it — nobody can say
"if we set this threshold, our false-alarm rate is at most 5%" because
the threshold was never calibrated against any notion of a null
distribution. It is tuned by eyeballing a handful of examples.

Conformal prediction (Vovk, Gammerman & Shafer, "Algorithmic Learning
in a Random World", 2005; see also Angelopoulos & Bates, "A Gentle
Introduction to Conformal Prediction", 2023 for a modern treatment)
gives a DISTRIBUTION-FREE, FINITE-SAMPLE-VALID way to attach an actual
p-value to "how unusual is this new response, given a reference set of
persona-consistent examples" — with a formal guarantee (stated below,
including the assumption it depends on) rather than an eyeballed cutoff.

## Method

Given a calibration set of n reference embeddings
`{e_1, ..., e_n}` — persona-consistent exemplar responses (from
`persona.example_responses`, or accumulated non-drifted turns from a
real conversation history) — and a nonconformity measure
`a(e, {other embeddings})` (here: mean distance to the k nearest
neighbors in the reference set, a standard conformal nonconformity
score for anomaly detection; see Laxhammar & Falkman, "Sequential
Conformal Anomaly Detection", 2011, for the same construction applied
to trajectory anomaly detection — this project adapts that general
technique to a new domain, LLM persona-response monitoring, rather than
inventing the underlying statistical method):

1. Compute each calibration point's LEAVE-ONE-OUT nonconformity score
   `a(e_i, {e_1,...,e_n} \\ {e_i})` — this is the null distribution.
2. For a new response embedding `e_new`, compute its nonconformity
   score `a(e_new, {e_1,...,e_n})` against the FULL calibration set.
3. The conformal p-value is:

       p = (1 + |{i : a(e_i, ...) >= a(e_new, ...)}|) / (n + 1)

   Small p means the new response is MORE unusual (higher
   nonconformity) than almost all calibration points — evidence of
   drift.

## Formal guarantee — and the assumption it depends on

**Claim**: under the null hypothesis that `e_new` is exchangeable with
the calibration set (i.e., drawn from the same underlying process, in
no particular order), `P(p <= alpha) <= alpha` for any `alpha` — the
false-alarm rate at threshold `alpha` is controlled AT MOST `alpha`,
regardless of the embedding space's actual distribution, sample size,
or dimensionality. This is a real, standard, correctly-cited
mathematical fact about conformal p-values (Vovk et al. 2005, Prop.
2.1 and its many restatements in the modern conformal-prediction
literature) — not something invented for this project.

**The assumption this depends on, stated plainly**: exchangeability of
the calibration set with the tested point UNDER THE NULL. In practice
this means: the calibration exemplars must actually represent the full
range of legitimate persona-consistent responses (varied topics,
lengths, registers within the persona's real scope), not a narrow or
stale sample. If the calibration set is small, unrepresentative, or
stale relative to how the persona is actually used, the guarantee is
formally still true (conformal validity always holds under
exchangeability) but practically WEAK — a valid test against the wrong
reference distribution still gives correct false-alarm control against
THAT reference distribution, it just may not be the comparison you
actually care about. Report the calibration set's size and give a
qualitative sense of its diversity alongside any p-value you cite.

## Honest status

- This has never been run against a real embedding backend with real
  LLM responses in this environment (no network access here to
  download `sentence-transformers`' model weights). It IS tested here
  with synthetic vectors to verify the p-value computation and the
  false-alarm-rate guarantee hold numerically (see
  `research/evaluation/conformal_validation.py`) — that is a
  code-correctness check on the STATISTICS, not evidence about real
  persona-response embeddings.
- Requires the real embeddings backend (`SPASM_SEMANTIC_BACKEND=embeddings`,
  `sentence-transformers` installed) for research use. The primary conformal
  path deliberately fails fast when real embeddings are unavailable; the old
  hashed-BOW fallback has been removed so a paper run cannot silently mix
  semantic and lexical representations. Lexical similarity remains available
  as an explicit baseline in `app.drift.semantic`.
- k (number of nearest neighbors) and the calibration set size both
  affect statistical power (how easily real drift is detected, as
  opposed to the false-alarm rate, which is guaranteed regardless) —
  this is not tuned or validated against real drift examples here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.drift.semantic import embed_text

def _get_vector(text: str) -> tuple[list[float], str]:
    """Return a real sentence embedding or fail explicitly.

    The research conformal path intentionally has NO silent hashed-BOW
    fallback. A lexical/hash representation can be retained as a separate
    baseline, but mixing it into the primary statistical detector would make
    the claimed semantic/conformal evaluation ambiguous.
    """
    real = embed_text(text)
    if real is None:
        raise RuntimeError(
            "Real sentence embeddings are required for conformal drift evaluation. "
            "Install research/requirements-research.txt and set "
            "SPASM_SEMANTIC_BACKEND=embeddings. "
            "The old hashed-BOW fallback was removed from the primary conformal path."
        )
    return real, "embeddings"


def _euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _knn_nonconformity(target: list[float], others: list[list[float]], k: int) -> float:
    """Mean distance to the k nearest neighbors in `others`. Standard
    nonconformity measure for conformal anomaly detection (Laxhammar &
    Falkman 2011) — low when `target` sits in a dense region of `others`
    (looks like a typical calibration point), high when it's far from
    everything (looks anomalous)."""
    if not others:
        return 0.0
    distances = sorted(_euclidean(target, o) for o in others)
    k_eff = min(k, len(distances))
    return sum(distances[:k_eff]) / k_eff


@dataclass
class ConformalResult:
    p_value: float
    nonconformity_score: float
    n_calibration: int
    k: int
    backend: str  # "embeddings"
    is_anomalous_at: dict = field(default_factory=dict)  # alpha -> bool, for a few common alphas

    def summary(self) -> str:
        flag = "ANOMALOUS" if self.p_value < 0.05 else "typical"
        return (
            f"conformal p={self.p_value:.4f} ({flag} at alpha=0.05), "
            f"nonconformity={self.nonconformity_score:.4f}, n_calibration={self.n_calibration}, "
            f"backend={self.backend}"
        )


def minimum_calibration_size_for_alpha(alpha: float) -> int:
    """The smallest achievable conformal p-value with n calibration points is
    1/(n+1) (when the new point is MORE extreme than every calibration
    point) — so detecting anything at significance level alpha REQUIRES
    n >= ceil(1/alpha) - 1. This is exact, not an approximation: with too
    few calibration examples, the test can NEVER reject at that alpha, no
    matter how extreme the response actually is. Callers should check
    `n_calibration` against this before trusting a `p_value >= alpha`
    result as "no drift detected" rather than "not enough calibration data
    to tell"."""
    return math.ceil(1 / alpha) - 1


def conformal_drift_test(response_text: str, calibration_texts: list[str], k: int = 3) -> ConformalResult | None:
    """Returns None if there isn't enough calibration data to run a
    meaningful test (need at least k+1 calibration examples — with fewer,
    the leave-one-out null distribution is degenerate and the p-value
    would be uninformative, not just imprecise; refusing to report a
    number here is the honest choice over reporting a meaningless one)."""
    if len(calibration_texts) < k + 1:
        return None

    backend_used = None
    calib_vectors = []
    for text in calibration_texts:
        vec, backend = _get_vector(text)
        calib_vectors.append(vec)
        backend_used = backend  # all calls use the same globally-configured backend
    new_vector, new_backend = _get_vector(response_text)
    assert new_backend == backend_used, "backend switched mid-computation — should never happen within one process"

    # Null distribution: each calibration point's LOO nonconformity score.
    null_scores = []
    for i in range(len(calib_vectors)):
        others = calib_vectors[:i] + calib_vectors[i + 1:]
        null_scores.append(_knn_nonconformity(calib_vectors[i], others, k))

    new_score = _knn_nonconformity(new_vector, calib_vectors, k)
    n = len(null_scores)
    n_at_least_as_extreme = sum(1 for s in null_scores if s >= new_score)
    p_value = (1 + n_at_least_as_extreme) / (n + 1)

    return ConformalResult(
        p_value=p_value, nonconformity_score=new_score, n_calibration=n, k=k, backend=backend_used,
        is_anomalous_at={alpha: p_value < alpha for alpha in (0.01, 0.05, 0.10)},
    )


def calibration_adequacy_report(n_calibration: int) -> dict:
    """Human-readable check: which common significance levels can this
    calibration set even in principle detect at? Use this to warn a caller
    (or a paper's methods section) BEFORE reporting a p-value as meaningful."""
    return {
        alpha: {
            "min_p_value_achievable": round(1 / (n_calibration + 1), 4),
            "can_detect_at_this_alpha": n_calibration >= minimum_calibration_size_for_alpha(alpha),
        }
        for alpha in (0.01, 0.05, 0.10, 0.20)
    }
