# Experiments

All scripts are in `research/experiments/`. **None have been
executed** — I have no network access in the environment I built
this in, so I could not run these against a real Groq model.
Every script is real, syntax-checked code that imports the actual
backend modules (not a reimplementation) — running them is on you.

## Scripts

| Script | Compares against spec section | What it produces |
|---|---|---|
| `baseline_vanilla.py` | § 15 Baseline A | Raw LLM responses, no persona, no detection |
| `baseline_persona_prompt.py` | § 15 Baseline B | Persona system prompt only |
| `baseline_detector.py` | § 15 Baseline C | Persona prompt + detection, no repair |
| `experiment_full_spasm.py` | § 15 Proposed method | Full pipeline: persona + detect + repair + verify |
| `experiment_adversarial.py` | § 14, 20 | Attack success/failure per adversarial category |
| `experiment_ablation.py` | § 22 | Full SPASM++ minus one component at a time |
| `experiment_multiturn.py` | § 21 | Stability vs. conversation length (1/5/10/20/30 turns) |
| `experiment_repair.py` | § 11, 17 | Before/after stability, operator, latency, token overhead per repair |

## Running them

```bash
cd research/experiments
python -m pip install -r ../requirements-research.txt   # just pyyaml + pytest, lightweight
source ../../backend/.venv/bin/activate                  # reuse the backend's venv for app imports
python baseline_vanilla.py
python baseline_persona_prompt.py
python baseline_detector.py
python experiment_full_spasm.py
python experiment_adversarial.py
python experiment_ablation.py
python experiment_multiturn.py
python experiment_repair.py
```

Edit `research/experiments/config.yaml` first to point at models you
actually have available — `GROQ_API_KEY` configured in `backend/.env`.

## Output

Every run writes one JSON file to `research/results/raw/`, named
`{script_name}_{timestamp}_{random_id}.json`, containing:
`experiment_id`, `timestamp`, `config` (the exact config used),
`n_records`, and `records` (per-item results with drift/repair
detail). This is the full provenance spec section 25/32 asks for.

## Turning raw results into tables/figures

Not yet implemented — `research/results/processed/`, `tables/`, and
`figures/` are currently empty placeholder directories. Once you've
actually run experiments, the pattern would be: load the JSON from
`results/raw/`, compute metrics via `research/evaluation/metrics.py`
+ `calibration.py` + `statistical_tests.py`, and save summary
tables/plots into `processed/` / `tables/` / `figures/`. I didn't
pre-build this aggregation layer because doing it against fabricated
example data would violate the project's own honesty rule — build it
against your first real run instead, and I'm glad to help write that
once you have real `results/raw/*.json` files to point it at.

## SPASM++ publication-critical upgrade experiments

### Sequential conformal

Run `research/evaluation/sequential_conformal_validation.py` first as a
numerical implementation check. Then run the real experiment with held-out
per-turn conformal p-values and compare:

- one-shot conformal
- sequential test-martingale

Report false-alarm control, detection delay, persistent-drift recall, and
conversation length.

### Multivariate attribution

Run the dimension-wise conformal detector with a separate calibration bank per
persona dimension. Report raw p-values, BH-adjusted q-values, attribution
precision/recall, and the fraction of cases marked insufficiently calibrated.

### End-to-end risk

For held-out data, count detector false alarms and repair-safety failures.
Use `compose_empirical_risk()` to compute exact one-sided component upper bounds
and the conservative union-bound system risk. Do not call the resulting number
a distribution-free guarantee unless the underlying component assumptions have
actually been established.

### Baselines

Use `research/baselines/nautilus_compass.py` for the public-method Nautilus-style
condition and `research/baselines/contextecho_protocol.py` for the ContextEcho
snapshot/probe and single-shot anchor condition. State clearly that these are
clean-room implementations/adapters rather than exact copies of the official
repositories.
