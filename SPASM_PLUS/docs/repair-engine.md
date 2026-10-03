# Repair Engine (Phase 6/7)

`backend/app/repair/engine.py` maps severity to a repair operator
(`context_reinforcement` / `persona_constraint_reinforcement` /
`strong_reanchor_regenerate` / `full_regenerate_and_reset`), builds
a reinforced prompt, calls the same provider to regenerate a
response, then **re-runs the drift detector on the new response**
before reporting success. `success` is only ever `true` if
`stability_after > stability_before` — repair never claims success
without checking.

## Known limitations

- Regeneration uses the same model/provider that produced the
  drifted response — there's no fallback to a stronger model on
  repeated repair failure yet.
- No cap on repair attempts per turn — a persistently-drifting
  conversation will attempt exactly one repair per detected drift
  event, and report `REPAIR FAILED` if it doesn't improve stability,
  rather than retrying automatically.
- Repair success rate, average latency, etc. are NOT EVALUATED —
  same reasoning as drift-detection.md: no fabricated numbers until
  real experiments run.
