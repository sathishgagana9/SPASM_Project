# SPASM-DriftBench

A benchmark for **runtime persona drift** — scope violations, domain
switching, persona-switch attacks, instruction conflicts, and
multi-turn drift — built around the 8 built-in SPASM++ personas.

**This is not claimed to be the first persona-drift benchmark.** It
is positioned specifically for the drift/repair scenarios SPASM++
targets, built from this project's own persona definitions.

## Files

| File | Records | What it covers |
|---|---|---|
| `prompts.jsonl` | 22 | In-scope / out-of-scope / borderline requests per persona, including "in-scope topic but the compliant answer must still refuse a sub-part" cases (e.g. Doctor being asked to diagnose) |
| `adversarial_prompts.jsonl` | 10 | Persona-switch attacks: direct domain switching, persona override, indirect override, authority manipulation, prompt injection, multi-turn manipulation, contradictory instructions |
| `multiturn_scenarios.jsonl` | 2 | Multi-turn drift — a persona contradicting an earlier stated commitment |
| `annotations.jsonl` | 1 (template) | The schema for human annotation — **unfilled**, see below |

## Label provenance — read this before using these labels as ground truth

Every record in `prompts.jsonl`, `adversarial_prompts.jsonl`, and
`multiturn_scenarios.jsonl` is tagged
`"label_source": "synthetic_author_generated"`. These labels were
written by whoever built this dataset (informed by the persona
definitions), not collected from independent human annotators. They
are a reasonable starting point for smoke-testing the detector and
for designing an annotation study — they are **not** validated
ground truth suitable for reporting accuracy/F1 numbers in a paper.

`annotations.jsonl` contains only the annotation schema (the fields
a real annotator would fill in — `persona_adherence`,
`scope_adherence`, per spec section 18) with placeholder/`None`
values. It needs to actually be annotated by real people before any
Cohen's kappa / Krippendorff's alpha number means anything.

## Regenerating

```bash
python research/datasets/build_dataset.py
```

Edit `build_dataset.py`'s `PROMPTS` / `ADVERSARIAL` / `MULTITURN`
lists to add scenarios, then re-run. Records are numbered
deterministically by list position, so re-running after an edit will
change downstream IDs — regenerate any dependent experiment results
after editing.

## Known gaps (for a Q1-caliber version of this benchmark)

- Only 22 core prompts across 8 personas — a real benchmark needs
  dozens to hundreds per persona for statistically meaningful
  per-persona metrics.
- No paraphrase sets yet (spec section 23 — robustness testing needs
  multiple phrasings of the same intent; none exist here yet).
- No indirect/implicit domain-switching examples (a request that
  drifts scope without an obvious keyword signal) — everything here
  is fairly direct.
- Not annotated by independent humans yet.
