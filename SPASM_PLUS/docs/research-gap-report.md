# Architecture / Research Gap Report

Written before implementation, per the "Step 2: Create an
architecture/research gap report" instruction.

## What existed before this upgrade

- Full product loop: persona CRUD → chat → rule-based drift detection
  (7 dimensions, no scope, `context` hard-coded to 1.0) → severity-
  adaptive repair → verification (only checked `after > before`) →
  dashboard.
- Provider abstraction (Ollama + generic cloud), streaming chat.
- 8 built-in personas with `scope` field added (previous session) but
  **not yet used by the detector** — persona compiler enforced scope
  via system prompt only; nothing checked it afterward.
- Solid test coverage for the existing pieces; no research
  infrastructure (empty `research/` directories).

## Gaps against the research-grade spec

| Gap | Severity | Addressed this session? |
|---|---|---|
| No scope dimension in detector | High — core spec ask | Yes (`scope.py`), with an important discovered limitation (see RESEARCH.md) |
| `context` hard-coded to 1.0 | High — explicitly called out as needing replacement | Yes (`context.py`), heuristic contradiction detection |
| Knowledge-boundary mention-vs-violation not distinguished | Medium — named failure mode in spec | Yes (`rules.py::check_knowledge_boundaries`) |
| Confidence = 1 - drift_score conflation | Medium | Yes — score/probability/confidence now separate (`scoring.py`) |
| No semantic/embedding layer | Medium | Partially — lexical proxy implemented and honestly labeled as such; real embeddings supported but optional/untested |
| No repair policy beyond severity lookup | Low-medium | Improved (violation-count-aware escalation, scope_reinforcement operator) — still a heuristic lookup, not a searched/learned policy |
| Repair verification only checked stability delta | Medium | Yes — now checks meaningful improvement, no new severe violation, usefulness heuristic |
| No benchmark dataset | High | Yes, pilot-scale (SPASM-DriftBench), synthetic labels only |
| No evaluation framework (metrics/calibration/agreement/stats) | High | Yes, pure-Python, unit-tested for correctness, actually executed in this sandbox |
| No experiment runners/baselines | High | Yes, real code using the actual app, not executed (no network here) |
| No database instrumentation for research provenance | Medium | Yes — `DriftEvent`/`RepairEvent` extended |
| No research documentation | Medium | Yes — RESEARCH.md, BENCHMARK.md, EXPERIMENTS.md, METHODOLOGY.md, REPRODUCIBILITY.md |

## What I found by actually testing, not just implementing

The scope dimension's lexical-similarity approach doesn't reliably
work for realistic phrasing — see RESEARCH.md's dedicated section.
This was discovered through actual execution partway through this
session (the pure-logic modules have no external dependencies, so I
could run them in this sandbox even without network access), and the
fix (making the classifier conservative rather than confidently
wrong) is reflected in the code, tests, and every doc that referenced
the old, incorrect claim.
