# SPASM++ Research Contribution and Publication Readiness

**Current research identity:**

> **SPASM++: Risk-Calibrated Closed-Loop Detection and Adaptive Repair of
> Persistent Persona Drift in LLM Agents**

This document is intentionally conservative about novelty. The repository now
contains the code paths for sequential conformal evidence, multivariate
attribution, end-to-end risk composition, real-embedding-only conformal
experiments, and public-method baseline adapters. Live model runs and human
annotation are still required before any numerical claim is publication-ready.

## 1. What changed in the novelty pass

### Contribution A — sequential / anytime-valid drift evidence

`backend/app/drift/sequential_conformal.py` maintains a test-martingale over
per-turn conformal p-values. It is designed for persistent drift rather than
independent one-shot decisions.

The implementation uses a power betting factor and raises an anytime alarm
when the e-value crosses `1 / alpha`.

**Important validity condition:** ordinary one-shot conformal p-values do not
become automatically anytime-valid merely by multiplying them. The formal
martingale interpretation requires the supplied per-turn p-values to satisfy
the appropriate conditional super-uniformity assumption under the null. The
code records this assumption explicitly and does not claim otherwise.

### Contribution B — attributable multivariate nonconformity

`backend/app/drift/multivariate_conformal.py` computes a conformal p-value for
each persona dimension and applies Benjamini-Hochberg FDR correction. The output
contains raw p-values, adjusted q-values, and the dimensions that provide
statistical evidence of drift.

This changes the research question from:

> "Did the response drift?"

to:

> "Which persona dimensions provide calibrated evidence of drift?"

The underlying conformal and BH procedures are established statistics; the
research contribution is their use as an interpretable, dimension-attributed
runtime drift layer for this application. The claim should remain an
application/methodology claim unless experiments establish something stronger.

### Contribution C — composed end-to-end risk ledger

`backend/app/drift/system_risk.py` links component risk budgets with a union
bound:

`P(detector false alarm OR repair safety failure) <= alpha_D + delta_R`.

The module also supports exact one-sided Clopper-Pearson upper bounds for held-
out empirical failure counts and then composes those bounds conservatively.

This is not new probability theory. The contribution is an auditable system-
level risk accounting layer that connects the detector and repair stages.

## 2. Literature boundary

Two directly relevant 2026 works must be treated as baselines/related work:

- **Nautilus Compass** (arXiv:2605.09863) describes black-box persona-drift
detection using BGE-M3 embeddings and positive/negative behavioral anchors.
- **ContextEcho** (arXiv:2605.24279) provides a long-session persona-drift
benchmark/protocol and evaluates a single-shot anchor mitigation.

These works mean that "persona drift detection with embeddings" and "long-
session persona drift" are not sufficient novelty claims by themselves.

The project also sits in an active conformal-risk literature. SConU applies
conformal significance testing to uncertainty in LLMs; SCoRE and related
selective conformal work study risk-controlled trust/abstention; and 2026 work
has studied group-conditional conformal risk control for language models.
Therefore SPASM++ must not claim that conformal risk control itself is new.
The defensible gap is the **specific sequential + attributable + repair-linked
persona-drift management pipeline**, subject to experimental validation.

## 3. Baseline policy

### Nautilus Compass

`research/baselines/nautilus_compass.py` is a clean-room implementation of the
publicly described positive/negative-anchor weighted-top-k cosine method using
BGE-M3. It is explicitly **not** the official Nautilus Compass repository.
Exact reproduction should use the authors' released code/data.

### ContextEcho

`research/baselines/contextecho_protocol.py` implements the public
snapshot-then-probe protocol and single-shot anchor mitigation condition.
ContextEcho is a benchmark/protocol, not a conventional detector. It would be
methodologically incorrect to pretend it is a directly interchangeable
classifier baseline.

## 4. Publication-critical experiments still outstanding

The code is prepared, but these cannot honestly be marked complete until they
are run:

1. Install `sentence-transformers` and run the conformal detector with real
   embeddings. The primary conformal path no longer silently falls back to
   hashed bag-of-words.
2. Generate and human-screen a sufficiently large calibration set. At
   alpha=0.05, at least 19 calibration examples are required merely to make the
   smallest possible conformal p-value <= 0.05; substantially more are
   recommended.
3. Run the adversarial suite against at least three model families.
4. Run the Nautilus-style baseline on the exact same held-out benchmark.
5. Run the ContextEcho-style long-session protocol/anchor condition on the
   same long-session benchmark where applicable.
6. Obtain two independent human annotators for a held-out subset and report
   Cohen's kappa plus raw agreement/class counts.
7. Tune thresholds and conformal/calibration parameters on development data
   only; never tune on the final test set.
8. Report F1, AUROC, AUPRC, FPR, calibration, repair success, persistence,
   utility loss, latency, token overhead, and confidence intervals.
9. Report ablations for sequential conformal, FDR attribution, adaptive repair,
   safety constraint, and verification/persistence.

## 5. Current readiness rating

These are **engineering/research-readiness ratings, not predictions of paper
acceptance**:

| Dimension | Current rating | Why |
|---|---:|---|
| Novelty potential | **8.0 / 10** | The research story now has temporal conformal evidence, attribution, and system-level risk composition rather than only a generic drift detector. |
| Algorithmic novelty | **6.5 / 10** | The underlying conformal, FDR, and bandit machinery is established; novelty is primarily the application/system formulation. |
| Experimental readiness | **6.0 / 10** | Scripts and protocols are prepared, but real multi-model runs are still outstanding. |
| Human-grounded validity | **4.0 / 10** | The repository still has synthetic labels; human annotation must be completed. |
| Reproducibility | **8.0 / 10** | Versioned modules, configs, calibration separation, tests, and baseline adapters are included. |
| Overall submission readiness | **6.0 / 10** | The implementation is substantially stronger, but live evidence is required before submission. |

The important distinction is: **the codebase can now support an 8+/10 novelty
story, but the paper does not earn that claim until the experiments demonstrate
that the proposed components provide measurable benefit.**

## 6. Claim wording to use in the paper

Prefer:

> We introduce a risk-calibrated closed-loop framework that combines sequential
> conformal drift evidence, dimension-attributed FDR control, adaptive repair,
> and verification for persistent persona-drift management.

Avoid:

> "We are the first system to detect persona drift."

Avoid:

> "We invented conformal monitoring / conservative bandits."

Avoid:

> "The system has an 8% failure guarantee"

unless the component assumptions and the required held-out validation have
actually been established.
