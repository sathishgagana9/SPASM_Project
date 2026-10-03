# Architecture (Phase 0 snapshot)

## Layering

```
UI (React)
  -> services/api.ts (fetch wrapper, /api/* via Vite proxy)
  -> FastAPI routers (app/api/*)
  -> SQLAlchemy models (app/models/*) via async session (app/db/session.py)
  -> SQLite (dev) — DATABASE_URL is the only thing that changes for Postgres
```

The frontend contains no business logic beyond form state and
display — no drift math, no repair logic, no API keys. That all
lives in the backend, per the "frontend must not contain
algorithms/credentials" rule in the source spec. As of Phase 0,
there is no drift/repair logic anywhere yet — `app/drift/`,
`app/repair/`, `app/evaluation/`, `app/providers/` are empty
packages reserved for Phases 1, 4, and 5.

## Why SQLite now, Postgres later

`DATABASE_URL` in `.env` is the single seam. SQLAlchemy's async
engine + `aiosqlite` driver behave close enough to
`asyncpg`/Postgres for the ORM layer that switching should mean
changing the URL and driver, not rewriting models — but this has
not been tested against a real Postgres instance yet.

## What's not decided yet

- Provider abstraction interface shape (Phase 1)
- Full persona schema (Phase 2) — current `Persona` model is
  intentionally minimal (name + description) to prove the pipe
  works before committing to a schema
- WebSocket vs SSE for live dashboard updates (Phase 8)
