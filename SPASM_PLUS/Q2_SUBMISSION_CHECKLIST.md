# Q2 Submission Checklist

This is the concrete task list implied by `RESEARCH_CONTRIBUTION.md`
§5, expanded with effort estimates and explicit pass/fail criteria.
Read `RESEARCH_CONTRIBUTION.md` first — this file assumes you've
already accepted its honest novelty accounting (the classifier gate
is not the contribution; the conformal detector and conservative
bandit are, and only if the items below are completed).

**No amount of further offline engineering moves novelty past what's
already built.** Every remaining item requires either (a) executing
something against a real model, (b) human judgment/labeling, or (c)
writing/positioning work only you can do credibly as the author. This
is not a list of things I can do for you from here.

## Tier 1 — blocking. Without these, there is no submission.

### 1.1 Run the adversarial red-team suite for real
- **Command**: wire a real `LLMProvider` (Groq, your API key) into `adversarial_evaluation.run_live()`, run all 144 items.
- **Effort**: ~1-2 hours of API calls (144 items × up to 3 turns × classifier latency), plus a short script to call `run_live` instead of `run_stub`.
- **Pass criteria**: a report with real ASR/DSR per category, not the stub sanity numbers.
- **What to actually look at**: is `multi_turn_escalation` DSR meaningfully lower than the single-turn categories? If yes, that's your most citable empirical finding — it validates the exact gap `intent_classifier.py` already claims exists. If no, that's ALSO worth reporting (it would mean history-awareness in the classifier prompt is working better than expected) — either outcome is real data, don't go in expecting a specific answer.

### 1.2 Run the conformal detector against real embeddings
- **Command**: `pip install sentence-transformers`, set `SPASM_SEMANTIC_BACKEND=embeddings`, re-run the typical/drifted comparison from our earlier session with a calibration set of **at least 19 examples** (the exact minimum for α=0.05, per `minimum_calibration_size_for_alpha`).
- **Effort**: ~30 minutes (mostly model download time).
- **Pass criteria**: does a real off-persona response get p < 0.05 where the lexical fallback failed to reach it? This is the single check that tells you whether §3.1's contribution is a real detector or just a validated formula with no practical power yet.

### 1.3 Train the bandit/conservative-bandit on real repair outcomes
- **Command**: `experiment_repair.py --policy learned` repeatedly against a live provider to accumulate real `(context, operator, reward)` tuples, then `train_repair_policy.py --train`.
- **Effort**: this is the expensive one — needs enough real drift events to accumulate meaningful bandit data. Budget for at least 200-300 repair events across varied personas/severities before trusting any learned weights.
- **Pass criteria**: does the trained policy's operator selection differ meaningfully from the lookup table on held-out contexts, and does it correlate with better outcomes? If you don't have enough data to say yes, report that honestly rather than presenting undertrained weights as a result.

### 1.4 Human-annotate a portion of the benchmark data
- **What**: `scope_benchmark_expanded.jsonl` (100 items) and `adversarial_redteam_suite.jsonl` (144 items) are currently author-labeled.
- **Minimum bar for Q2**: get at least 2 independent annotators on a meaningful subset (50-100 items is a reasonable target), compute Cohen's kappa or Krippendorff's alpha (`research/evaluation/annotator_agreement.py` already exists for this), and report it. A kappa below ~0.6 is itself a finding worth discussing, not just a number to hit.
- **Effort**: the actual labor-intensive item on this list — budget real annotator time, not just your own pass.

## Tier 2 — required for the paper to survive review, not just to be true

### 2.1 Rewrite RESEARCH.md's related work
- Cite every row in `RESEARCH_CONTRIBUTION.md` §1's table, especially the tourism gatekeeper paper (arXiv:2509.21367) and Nautilus Compass/ContextEcho.
- **Explicitly state, in the paper's own words**, that the gate architecture matches prior art and position the contribution as the conformal detector + conservative bandit adaptation — don't make a reviewer discover this by finding the papers themselves. Reviewers respond far better to "we are aware of X and differ in Y" than to being the one who points out X exists.
- **Effort**: a few hours of careful writing, not research — the citations are already gathered.

### 2.2 Reframe the abstract/introduction/title
- Do NOT lead with "a framework that prevents persona drift via classification." Lead with the conformal/conservative-bandit angle: something like *"a persona-drift correction framework using conformal anomaly detection and safety-constrained bandit repair, applied to adversarial persona-switching in task-oriented LLM assistants."*
- This is a positioning task, not an engineering one — but get it wrong and reviewers anchor on "another guardrail paper" before reading further.

### 2.3 Decide and defend the cost values in `decision_theory.py`
- The default costs (`C_FA=3.0`, risk-tier multipliers) are explicitly illustrative. A reviewer will ask where these numbers come from.
- Either (a) run a small user study / expert elicitation to justify specific values, or (b) present the sensitivity-analysis table itself as the contribution ("we show how the threshold varies with the cost ratio; a deployer chooses their own point") rather than asserting one correct number. Option (b) is faster and arguably more honest.

## Tier 3 — strengthens the paper, not strictly required

- Extend the conformal detector to a **rolling-window** variant (accumulate a window of recent turns as the "test set" rather than n=1) for more statistical power — noted as future work in `conformal.py`, not built.
- A small human evaluation ("do repaired responses seem more in-character to real users than unrepaired ones") — mentioned in the original novelty-review document from early in this project, never built. Real user-study logistics, not something I can produce.
- Extend the adversarial suite with **obfuscated/encoded attacks** (base64, leetspeak, translated-then-back) as a 7th category, if reviewers of an earlier draft ask for it.

## What "novelty 7-8.5" actually requires, stated plainly

It requires Tier 1 completed with results that hold up — i.e., the conformal detector shows real power on real embeddings, and the conservative bandit shows a real, measured safety/performance trade-off on real repair data, not just a synthetic stress test. A framework with correct math and zero live validation is not more novel than one with only some of the math — novelty in an applied paper is earned by what the numbers show, not by how much code exists. Nothing above is optional if the target is a genuine, defended 7+; skipping Tier 1 and submitting anyway is very unlikely to be treated as one.
