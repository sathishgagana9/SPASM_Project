# Repair-loop guarantees: no-worse-off and bounded regeneration

This is the formalization the novelty-review flagged as missing:
*"a no-worse-off guarantee: repaired output is never accepted unless
it strictly dominates the original on stability without new
violations; or bound the max number of regenerate cycles needed."*
Implemented in `backend/app/repair/engine.py::repair_until_verified()`.
This document states the two properties precisely, gives a proof
sketch appropriate for an applied-AI paper (not a mechanized formal
proof), and — just as important — states exactly what assumptions
the proof depends on, so you can check they hold before citing either
property without qualification.

## Setup and notation

- `D(P, r)` — the detector's `overall_stability` for response `r`
  under persona `P` (deterministic given `r`; see assumption A1
  below). Range `[0, 1]`, higher = more stable/persona-adherent.
- `r_0` — the original (pre-repair) response. `s_0 = D(P, r_0)`.
- An **attempt** at cycle `i` produces a candidate response `r_i` via
  some repair operator, with `s_i = D(P, r_i)`.
- `best_i` — the best candidate seen through cycle `i`, defined as
  `argmax_{j <= i} s_j` where `j=0` (the original) is always a
  candidate in this set. This is exactly what the loop's `best`
  variable tracks.
- `MAX_CYCLES` — a fixed integer bound (default 3, caller-configurable).

## Property 1 — No-worse-off

**Claim**: for every cycle `i`, `D(P, best_i) >= D(P, r_0) = s_0`.
Equivalently: the stability of whatever `repair_until_verified()`
returns is never less than the stability of the un-repaired original.

**Proof sketch**: by induction on `i`.//
- Base case (`i = 0`, no repair attempts yet): `best_0 = r_0`, so
  `D(P, best_0) = s_0 >= s_0`. Trivially true.
- Inductive step: assume `D(P, best_{i-1}) >= s_0`. The loop body
  (see `repair_until_verified`, the `if attempt["stability_after"] >=
  best["stability_after"]` check) sets `best_i = r_i` if
  `s_i >= D(P, best_{i-1})`, and `best_i = best_{i-1}` otherwise. In
  the first case, `D(P, best_i) = s_i >= D(P, best_{i-1}) >= s_0` by
  the inductive hypothesis. In the second case,
  `D(P, best_i) = D(P, best_{i-1}) >= s_0` directly. Either way the
  invariant holds. ∎

This is a **structural** guarantee — it holds by construction of the
comparison-and-replace logic, not by hoping the repair operator helps.
A repair operator that reliably makes things worse simply never gets
selected as `best`; the function degrades to returning `r_0` unchanged
(recorded as `success=False`,
`quality_flags=["no_repair_attempt_met_no_worse_off_bar"]`), which is
the documented, honest failure mode — not a silent regression.

### Assumptions this depends on (check before citing without qualification)

- **A1 — `D` is deterministic given `r`.** `detect_drift()` is a pure
  function of `(persona, response_text, user_prompt, history)` — no
  randomness, no external state — so re-scoring the same response
  twice always gives the same `overall_stability`. This holds for the
  current rule-based detector. **It does NOT automatically hold if you
  swap in the LLM-judge feature (`judge.py`) at nonzero temperature**
  — a judge score is a random variable in that case, and the proof
  above needs `D` to be replaced with `E[D]` or the judge needs
  temperature 0 (see judge.py's own recommendation) for the guarantee
  to hold in the stated form.
- **A2 — the comparison is by `overall_stability` alone.** The
  `_verify()` function's *acceptance* criteria (meaningful
  improvement, no new severe violation, usefulness) are independent
  of this guarantee — Property 1 is about what gets *returned*, not
  what gets marked `success=True`. A response can be the best-seen
  candidate (satisfying Property 1) while still failing verification
  (e.g. it didn't improve *enough* to pass `MEANINGFUL_IMPROVEMENT_THRESHOLD`)
  — that's `success=False` with a non-regressed `repaired_content`,
  by design.
- **A3 — no adversarial interleaving.** This function is not
  thread-safe against concurrent mutation of `drift_event` mid-loop;
  the proof assumes single-threaded, sequential execution, which
  matches how it's called today (one repair loop per drift event).

## Property 2 — Bounded regeneration

**Claim**: `repair_until_verified()` terminates within at most
`MAX_CYCLES` repair attempts (LLM calls), for any input.

**Proof sketch**: the loop body is a `for cycle in range(1, max_cycles
+ 1)` with no unbounded inner loop, no recursion, and no `continue`
that skips the loop-variable increment — every iteration either
returns early (on `attempt["success"]`) or falls through to the next
`cycle` value. Python's `range` guarantees exactly `max_cycles`
iterations in the absence of early return. Therefore the number of
`repair()` calls (each a bounded number of LLM calls — one, per
`repair()`'s own implementation) is `<= max_cycles`. ∎

This is a much easier property than Property 1 (it's closer to "read
the code," not an argument about semantics) but it's exactly what
Part A's review asked to have stated explicitly, because the OLD
`repair()` function (v2) had no loop at all — it made exactly one
attempt and returned regardless of success, which technically
satisfies "bounded" trivially (bound = 1) but couldn't ever recover
from an operator that didn't work. The v3 loop trades a slightly
weaker *tightness* of the bound (up to `MAX_CYCLES` calls instead of
exactly 1) for the ability to actually reach a verified state when
the first-choice operator doesn't work — report both the bound and
the empirical distribution of `cycles_used` across your benchmark
runs (already logged per-attempt) so a reviewer can see how often you
actually use more than 1 cycle in practice, not just that you're
capped at 3.

## What would break each guarantee (read before citing)

| If you change... | Property 1 (no-worse-off) | Property 2 (bounded) |
|---|---|---|
| Detector becomes stochastic (temperature > 0 judge feature) | Breaks as stated; needs expectation-based restatement | Unaffected |
| `max_cycles` set to 0 | Vacuously holds (`best_0 = r_0`) | Vacuously holds (0 LLM calls) |
| A repair operator itself calls `repair_until_verified()` recursively | Unaffected | Breaks — recursion isn't bounded by this argument, would need a separate induction on recursion depth |
| Concurrent/parallel repair of the same event | Breaks (A3 violated) — would need a lock or an explicitly serialized comparison | Per-call bound still holds; aggregate system throughput reasoning is separate |

## What to actually report in the paper

1. State Property 1 and Property 2 as given above, WITH the
   assumptions table — reviewers respond well to stated preconditions,
   poorly to guarantees that turn out to have unstated caveats.
2. Report the empirical distribution of `cycles_used` from your real
   experiment runs (mean, median, max observed vs. the configured
   `max_cycles`) — this shows the bound is meaningful, not just
   technically true because it's rarely approached (or, if it's
   frequently hit, that's a finding about how hard drift is to repair
   in one attempt, worth discussing).
3. If you use the LLM-judge feature in fusion.py for anything that
   feeds back into repair decisions, explicitly note whether you ran
   it at temperature 0 (required for Property 1 as stated) — and if
   not, restate the guarantee in expectation and say so.
