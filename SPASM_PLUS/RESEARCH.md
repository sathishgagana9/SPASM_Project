# SPASM++ as a research framework

## Positioning

SPASM++ is a **model-agnostic runtime framework for detecting,
quantifying, and mitigating persona drift in multi-turn LLM
conversations**, through structured persona constraints, a
multidimensional hybrid drift detector, adaptive repair, and
verification.

The contribution is **not** "an AI chatbot with personas." It is:

1. A structured persona representation (§ below) and a compiler that
   turns it into runtime constraints + a runtime "expected behavior"
   reference the detector can check against.
2. A hybrid (rule-based + lexical-semantic) runtime drift detector
   across 8 dimensions, with an explicit fix for the naive
   "forbidden-word-appears = drift" failure mode (refusal-vs-violation
   distinction, boundary mention-vs-violation distinction).
3. A severity- and violation-aware adaptive repair policy with
   verification that checks more than "did the score go up."
4. A benchmark (SPASM-DriftBench) and evaluation methodology built to
   actually test the above, including adversarial persona-switch
   attacks and multi-turn drift.
5. Honest, uncalibrated-by-default metrics with a real path to
   calibration once labeled data exists.

## Formal persona representation

```
P = {
  identity, tone, scope,
  personality_traits, goals, values,
  behavior_rules, knowledge_boundaries,
  response_constraints, forbidden_behaviors,
  example_responses
}
```

Implementation: `backend/app/models/persona.py` (storage),
`backend/app/services/persona_compiler.py` (P → runtime system
prompt + P → structured summary the detector uses).

## Drift detection formalism

```
D_t = f(P, U_t, R_t, H_t)
```

— persona, the triggering user request, the generated response, and
conversation history. Implementation: `backend/app/drift/detector.py`
orchestrates `rules.py` (deterministic), `scope.py` (scope-adherence
classification using U_t vs P.scope, refusal-pattern-aware), `context.py`
(H_t-based contradiction detection), and `semantic.py` (the
similarity primitive scope.py and context.py build on).

## Scoring formalism

```
PS(r, P, H) = Σ_d w_d · S_d(r, P, H)     over d in DIMENSIONS
```

8 dimensions: identity, scope, behavior, tone, goals, knowledge,
instruction, context. Default weights are equal
(`backend/app/drift/scoring.py::DEFAULT_WEIGHTS`) — **PROVISIONAL,
not validated**. `drift_score`, `drift_probability`, and `confidence`
are computed as three distinct, separately-defined quantities (see
`scoring.py` module docstring) rather than collapsed into one number.

## What "validated" would require, and hasn't happened yet

Every heuristic in this codebase is a real, deterministic function of
real inputs — nothing is fabricated or randomized. But **none of it
has been validated against labeled data.** Concretely, before any
accuracy/F1/AUROC number from this system should appear in a paper:

1. SPASM-DriftBench (`research/datasets/`) needs real human
   annotations (currently only synthetic, author-written labels —
   see `research/datasets/README.md`).
2. Thresholds (`scoring.py`, `scope.py`'s `OUT_OF_SCOPE_THRESHOLD`/
   `IN_SCOPE_THRESHOLD`) need to be selected on a dev split via
   `research/evaluation/calibration.py::select_threshold_from_dev_set`,
   not hand-picked as they currently are.
3. `drift_probability` needs actual calibration (Brier score / ECE)
   against labeled outcomes — `research/evaluation/calibration.py`
   has the machinery, no calibration has been run.
4. The lexical similarity backend (default) should be compared
   against the optional embedding backend to quantify how much
   "semantic" analysis actually buys you — not assumed.
5. Every experiment script in `research/experiments/` needs to
   actually be run (against your own Groq-backed models — I have no
   network access in the environment I built this in) and the
   results need to go through `research/evaluation/` before any
   number is reported.

## Known research-honesty status of every claim in this codebase

| Claim | Status |
|---|---|
| "Detects the refusal-vs-violation distinction" | Partially true, empirically verified, with an important caveat below |
| "Context drift detection" | Implemented as regex/lexical-overlap contradiction matching, real but narrow — will miss most real contradictions, see `context.py` docstring |
| "Semantic analysis" | Real, but lexical cosine similarity by default, not neural embeddings — see `semantic.py` docstring |
| Any accuracy/F1/AUROC/kappa/alpha number | NOT YET EVALUATED anywhere in this repo — no experiment has been executed |
| Cross-model robustness | Architecturally supported (provider-agnostic), NOT YET TESTED across multiple models |

## A finding worth flagging prominently: the scope dimension's real limitation

While building this I actually ran the scope classifier against the
spec's own worked examples (something I could do without a live LLM,
since it's pure string logic) and found a genuine bug: the lexical
similarity backend gave **identical (zero) similarity scores** for
"Explain linked lists" (in-scope) and "How do I make biryani?"
(out-of-scope) against Teacher's scope description. Enriching the
scope text with more subject vocabulary didn't fix it — specific
questions ("quadratic equations", "World War I") essentially never
share literal tokens with category-level scope descriptions
("mathematics", "history"), regardless of whether they're in-scope.

**The fix I made**: the classifier no longer confidently flags a
violation from low similarity alone (that was causing false
positives on ordinary in-scope questions) — it only does that
reliably for the *refusal* side of the distinction (pattern-matching
"I can't help with that" is not similarity-dependent and works fine).
This means, honestly: **with the default lexical backend, the scope
dimension can confirm a persona *correctly refused*, but it cannot
reliably catch a persona that *silently answers* an out-of-scope
question without using refusal language** — that specific failure
mode (a Teacher persona giving a real biryani recipe with no refusal
language at all) is NOT reliably caught by this dimension as
currently built. It's still nominally checked (won't crash, returns a
mild `low_signal_not_flagged` score) but won't drive `detected=True`
on its own.

What still catches that case:
1. **The compiled system prompt's explicit scope instructions** (`persona_compiler.py`) — the primary defense, prompt-engineering based, not code-enforced (see the caveat at the top of this doc).
2. **Explicit `forbidden_behaviors`/`knowledge_boundaries` phrases**, if populated with words that actually appear in a violating response (works well for "I can diagnose..." style assertions, does NOT work for content that never uses give-away meta-vocabulary, like cooking instructions that never say "cooking" or "recipe").
3. **The optional real embedding backend** (`SPASM_SEMANTIC_BACKEND=embeddings`), untested here but architecturally the correct fix for this class of problem — genuine semantic similarity would likely separate these cases meaningfully better than bag-of-words.

I'm flagging this as prominently as I can because it directly affects
what you should expect from the acceptance test in the README —
Teacher declining to answer the biryani question depends almost
entirely on the model actually following the system prompt
instruction, not on the detector catching it after the fact if the
model doesn't comply.
