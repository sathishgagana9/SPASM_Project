# RAISE — Role Alignment & Integrity Stability Engine

*Consistency in Every Interaction*

*(formerly released as Anchora / "Real World Persona Drift Detection and Correction Framework", and before that SPASM++ — Persona Stability, Adaptation, and Self-Repair System)*

**Status: ChatGPT/Claude-style redesign complete**, layered on top of
the Phase 0–7 core loop (persona → chat → drift detection → repair →
verify). The app is now a three-column workspace — sidebar (new
chat, personas, chat history), center (streaming chat), right panel
(live persona/drift monitor) — with 8 built-in role-based personas
whose scope is actually enforced via the system prompt, real chat
history (rename/delete/auto-titled/persistent), Research and
Settings as working pages (no more locks), and streaming responses
from Groq (Ollama support was removed entirely — see "Provider"
section below).

**Read this before assuming persona scope enforcement is airtight:**
"Teacher refuses to explain biryani" is implemented as a strong,
explicit system-prompt instruction (see
`backend/app/services/persona_compiler.py` and
`docs/persona-system.md`) plus the existing drift detector as a
second layer. That is prompt engineering, not a code-level
guarantee — smaller/local models can still ignore it. I could not
verify this against your actual `llama3.2:3b` model (no network
access in the environment I built this in) — you need to run the
acceptance test yourself (see below) and tell me what actually
happens.

## What's actually built right now (Phases 0–7 + Persona Dashboard)

- Monorepo scaffold (`frontend/`, `backend/`, `research/`, `docs/`)
- **Provider abstraction** (`app/providers/`) — Groq is the only
  provider (Ollama support was removed entirely). `GroqProvider`
  implements the `LLMProvider` interface. Real HTTP calls, real
  error handling, and a clear error at construction time if
  `GROQ_API_KEY` isn't set.
- **Persona Dashboard** (the main landing page) — persona cards
  showing generic labels ("Persona 1", "Persona 2", …), never the
  internal name, with live Connect / Disconnect / Test Connection /
  Run / Stop actions and a real summary strip (Total Personas,
  Connected, Running, Errors, Available Providers) — all computed
  from actual persona rows, not mocked.
- **Persona Studio** (Advanced Settings) — full schema editor; the
  internal reference name is tucked behind an "Advanced" section and
  never rendered as an identity anywhere else in the app.
- **Chat system** — real conversations, real messages, calls the
  configured provider's live LLM.
- **Drift detection** — rule-based heuristic estimator across 7
  dimensions, honestly documented as provisional, not a trained
  classifier. `docs/drift-detection.md`.
- **Repair engine** — severity-adaptive, regenerates via the
  provider, re-verifies before ever claiming success.
  `docs/repair-engine.md`.
- **Drift Monitor page** — real stability chart + timeline.
- **System Status page** (formerly "Overview") — real
  backend/provider status.
- pytest tests: health, persona CRUD, drift detector, repair engine
  (stub provider, no live LLM needed).

## A note on how this was built

This scaffold was generated in a sandboxed environment with no
network access, so I could not run `npm install` or `pip install`
here to boot a live dev server. I verified what I could without
those:

- Backend: `python -m py_compile` on every module (syntax-valid) —
  but the actual FastAPI/SQLAlchemy runtime behavior has **not**
  been executed end-to-end. Run the test suite yourself (steps
  below) before trusting it.
- Frontend: ran `tsc` against each file in isolation (no real type
  errors — the only errors were "missing `@types/react`", which
  resolves once you `npm install`).

The new drift/repair tests (`test_drift.py`, `test_repair.py`) use
synthetic personas and a stub provider specifically so they run
without any live LLM — I could confidently write and syntax-check
those, but the actual chat endpoint calling a real Groq
model has not been exercised end-to-end by me.

Please run the setup below on your machine and tell me what breaks
— I'll fix it from there.

## Prerequisites

- Python 3.11+
- Node.js 18+
- A [Groq](https://console.groq.com) API key (free) — this is the default provider now, no local model needed
- (Optional) Docker + Docker Compose, if you'd rather not install
  Python/Node locally

## Setup — local (no Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env          # edit as needed
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the interactive API docs.

### If you already had a `spasm.db` from before this update

The schema gained more columns again — `DriftEvent` now also carries
`persona_switch_attempt`, `requested_role`, and `requested_domain`
(added for the intent-classifier / persona-boundary-enforcement
pipeline — see `backend/app/drift/intent_classifier.py`), on top of
the research instrumentation from earlier updates
(`drift_probability`, `detector_version`, `threshold_version`,
`scope_classification`, `scope_similarity`, `context_contradictions`,
`stability_improvement`, `token_overhead`, `quality_flags`). Same
story as every previous update — no Alembic migration wired up yet,
so SQLite won't add these to an existing file. For local dev:

```bash
cd backend
rm -f spasm.db      # you'll lose existing personas/conversations
uvicorn app.main:app --reload --port 8000   # recreates schema AND auto-seeds the 8 built-in personas
```

You no longer need to run `scripts/seed_personas.py` manually — the
backend seeds the 8 built-in personas (Teacher, Lawyer, Doctor,
Chef, Customer Support, Coding Expert, Research Assistant, Financial
Advisor) automatically on first startup if they don't already exist.
The script still exists for re-running it explicitly.

Run tests:

```bash
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. The Vite dev server proxies `/api`
to `http://localhost:8000`, so start the backend first.

### Seed example personas (optional)

Five ready-made personas — Study Mentor, a health-info assistant, a
legal-info assistant, a customer support agent, and a fitness coach
— so you have something to activate and chat with immediately
instead of building one from scratch:

```bash
cd backend
source .venv/bin/activate
python scripts/seed_personas.py
```

Safe to re-run; it skips personas that already exist by name. The
health/legal ones are deliberately configured with real boundaries
(`knowledge_boundaries`, `forbidden_behaviors`) that keep them
pointing people to an actual doctor/lawyer rather than pretending to
be one — worth reading `app/seed_data/personas.json` to see how
that's expressed in the schema.

## Setup — Docker

```bash
docker compose up --build
```

Frontend: `http://localhost:5173` · Backend: `http://localhost:8000`

## Groq setup (the only provider — Ollama support was removed entirely)

1. Create a free key at [console.groq.com](https://console.groq.com) → API Keys
2. In `backend/.env`:
   ```env
   GROQ_API_KEY=your_groq_key_here
   ```
3. Pick a current model name from [console.groq.com/docs/models](https://console.groq.com/docs/models) — model availability changes, `openai/gpt-oss-20b` (fast) or `openai/gpt-oss-120b` (larger) are reasonable defaults as of this writing, but check before assuming a name is still live. Groq has deprecated several models mid-2026, including `llama-3.3-70b-versatile` and `llama-3.1-8b-instant` — if you were following an older guide that recommended either of those, use the `gpt-oss` models above instead.
4. Without `GROQ_API_KEY` set, the app will raise a clear error the moment it tries to generate a response (`GroqProvider` checks for the key at construction time) rather than failing confusingly later.

With this configured, System Status's "Groq Provider" card should show `connected`, and every provider selection in the app (Dashboard, Chat) is Groq — there's nothing else to choose.

## Environment variables

See `.env.example` for the full list with comments.

## Project structure

```text
spasm-plus/
├── frontend/          React + TS + Vite + Tailwind
├── backend/           FastAPI + SQLAlchemy + SQLite
│   └── app/
│       ├── api/       route handlers
│       ├── core/      config
│       ├── db/        session/engine
│       ├── models/    SQLAlchemy models
│       ├── schemas/   Pydantic request/response models
│       ├── providers/ (empty — Phase 1: LLM provider abstraction)
│       ├── drift/     (empty — Phase 4: drift detection)
│       ├── repair/    (empty — Phase 5: repair engine)
│       └── evaluation/(empty — Phase 12: evaluation harness)
├── research/          datasets/experiments/results (empty scaffolding)
└── docs/              architecture notes
```

## Research framework

This project now also includes a research-grade layer on top of the
product: an 8-dimension hybrid drift detector (scope-adherence with
refusal-vs-violation distinction, real multi-turn context-drift
detection, lexical-semantic similarity), an explicit repair policy
with richer verification, SPASM-DriftBench (a benchmark dataset), and
a full evaluation/experiment framework. **None of the research
experiments have been executed** — see `RESEARCH.md`,
`BENCHMARK.md`, `EXPERIMENTS.md`, `METHODOLOGY.md`, and
`REPRODUCIBILITY.md` for what's real, what's validated, and what
still needs to be run.

## Acceptance test (run this yourself — I couldn't)

1. Start backend + frontend, confirm Groq shows connected on System Status.
2. Click **New Chat** → select **Teacher** → model a current Groq model name (e.g. `openai/gpt-oss-20b`) → Start Chatting.
3. Send: `Explain linked lists.` → expect a real academic explanation.
4. Send: `How to make biryani?` → expect a polite decline explaining it's outside Teacher's scope, **not** a recipe. This depends almost entirely on the model following the system prompt instruction — see the "scope dimension" finding below, which I verified by actually running the code: if the model doesn't comply, the detector likely won't catch it after the fact either (with the default configuration, no `forbidden_behaviors` populated for this).
5. Start a new chat with **Chef**, ask the same biryani question → expect a real recipe.
6. Throughout, confirm the right panel updates (alignment %, drift level, scope) without a page reload.
7. Rename the Teacher conversation from the sidebar, refresh the page, confirm the name persisted.
8. Delete a conversation, confirm it's gone and no orphaned drift/repair rows remain (there's a test for this — `pytest tests/test_conversations.py` — but confirming it via the UI is still worth doing).
9. Turn off monitoring in Settings, send a message, confirm the right panel shows "Monitoring temporarily unavailable" instead of blocking the response.
10. Temporarily set an invalid `GROQ_API_KEY` and restart the backend, send a message, confirm you get a clean "AI provider unavailable"/auth-error card with Retry — not a raw 502.

## Known limitations (being upfront)

- **Scope enforcement is prompt-based, not code-enforced.** Covered above — don't treat step 4 passing as a permanent guarantee across all models/phrasings.
- **Streaming + repair interaction:** if drift is detected on a streamed response, the repair step runs *after* the stream completes and replaces the visible text — so the user briefly sees the original (drifted) response, then it's swapped for the repaired one. This is disclosed in the UI via the "repaired response" tag, but it's a visible swap, not seamless.
- **Light theme toggle is stored but not visually implemented.** Settings lets you pick it and it's persisted, but I only built the dark theme's actual styling — flipping the toggle won't currently change any colors. Flagging this rather than pretending it works.
- **The scope dimension has a real, empirically-verified limitation** — I found this by actually running the code, not just reasoning about it. The default lexical-similarity backend cannot reliably distinguish "answered an out-of-scope question" from "answered an in-scope question with no shared vocabulary with the scope description" (both score zero similarity — e.g. "Explain linked lists" and "How do I make biryani?" against Teacher's scope). Confidently flagging that as a violation caused false positives on ordinary in-scope questions, so I made it conservative instead: it reliably confirms *appropriate refusals*, but does NOT reliably catch a persona that *silently answers* an out-of-scope question without refusal language. See `RESEARCH.md`'s dedicated section on this for the full explanation and what would actually fix it (real embeddings, not currently configured).
- **Chat history search** (mentioned as "if practical" in the spec) isn't implemented — the sidebar list isn't filterable yet.
- **Everything above is static/logical verification only** (syntax checks, unit tests against stub/local-only scenarios, prompt-content assertions) — I have no network access in the environment I built this in, so nothing involving your actual Groq/model behavior has been run. That's on you to confirm.

## Phase plan

✅ Phase 0 Foundation · ✅ Phase 1 Provider abstraction · ✅ Phase 2
Persona Studio · ✅ Phase 3 Chat · ✅ Phase 4 Drift detection · ✅
Phase 5 Drift classification/severity · ✅ Phase 6 Repair engine ·
✅ Phase 7 Repair verification · 🔲 Phase 8 full live dashboard
telemetry (waveform/dimension monitor beyond the current Drift
Monitor page) · 🔲 Phase 9 proactive context protection · 🔲 Phase 10
Model Arena · 🔲 Phase 11 StressBench · 🔲 Phase 12 evaluation
harness · 🔲 Phase 13 research dashboard · 🔲 Phase 14 broader test
coverage · 🔲 Phase 15 security/perf hardening · 🔲 Phase 16 UI
polish · 🔲 Phase 17 full docs.

Tell me what breaks when you run this locally, and/or which of the
remaining phases you want next — I'd rather build the next real
piece than pad this with more scaffolding.

## SPASM++ research upgrade

The research layer now includes a stronger temporal/statistical path:

```text
LLM response
   -> per-turn conformal p-value
   -> sequential test-martingale
   -> dimension-wise conformal p-values
   -> BH-FDR attribution
   -> repair policy
   -> verification + persistence
   -> end-to-end risk ledger
```

Primary research files:

- `backend/app/drift/sequential_conformal.py`
- `backend/app/drift/multivariate_conformal.py`
- `backend/app/drift/system_risk.py`
- `research/baselines/`
- `research/ANNOTATION_PROTOCOL.md`
- `FINAL_RESEARCH_READINESS.md`

The primary conformal path requires real sentence-transformer embeddings and
will fail fast rather than silently using the old hashed-BOW fallback. Use
`SPASM_SEMANTIC_BACKEND=embeddings` for research runs.

See `RESEARCH_CONTRIBUTION.md` for the conservative novelty accounting and the
exact list of experiments that still require live model access and human
annotation.
