# Reproducibility

## Environment

```bash
cd backend
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r ../research/requirements-research.txt
```

## Regenerate the dataset

```bash
python research/datasets/build_dataset.py
```

## Run the offline test suite (no live model needed)

```bash
cd backend
pytest                             # app tests: detector, repair, personas, conversations, providers
cd ../research
pytest tests/                      # evaluation-utility correctness tests
```

## Run experiments (needs `GROQ_API_KEY` configured in `backend/.env`)

See `EXPERIMENTS.md` for the full list and what each produces.

## What's deterministic vs. not

- **Deterministic**: the rule-based detector dimensions (identity,
  behavior, tone, goals, knowledge, instruction) given the same
  response text; the scope classifier given the same
  (prompt, scope, response) triple; bootstrap CIs/tests (fixed seed=42 by default).
- **Non-deterministic**: LLM generation itself (temperature > 0 by
  default in `config.yaml`), so re-running an experiment against a
  live model will not reproduce byte-identical responses — only the
  detector/repair logic applied to whatever the model returns is
  deterministic. Set `temperature: 0` in config.yaml for closer-to-deterministic
  generation if that matters for your comparison.

## Detector/threshold versioning

Every `DriftEvent` (in the database) and every experiment record
includes `detector_version` and `threshold_version`
(`backend/app/drift/scoring.py`). If you change detector logic or
thresholds, bump these strings — old results stay attributable to
the version that produced them rather than silently becoming
ambiguous.

## Known gaps for full reproducibility (remaining work)

- No `requirements.txt` lockfile with pinned exact versions (currently
  `>=`/`==` ranges) — pin exact versions before archiving a submission.
- No Docker image capturing the exact runtime — `docker-compose.yml`
  exists for running the app, but wasn't built with experiment
  reproducibility (exact library versions frozen) as a goal.
- No code-version stamping (git commit hash) in experiment output —
  ~~add `git rev-parse HEAD` to `common.py::save_results`'s payload~~
  **done** — every result file now includes `git_commit` (best-effort,
  `None` if not run inside a git repo).
