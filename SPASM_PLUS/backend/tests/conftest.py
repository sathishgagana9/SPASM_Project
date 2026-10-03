"""
Session-wide test fixture: creates the DB schema once before any test
runs.

## Why this was needed (bug this fixes, unrelated to any one test file)

`app.main.on_startup()` is the only place `init_db()` (which runs
`Base.metadata.create_all`) is called — but it's registered via
FastAPI's `@app.on_event("startup")`, which only fires when the
app's lifespan is actually triggered. Every existing test uses
`httpx.ASGITransport(app=app)` directly, which does NOT run lifespan
events by default. So the entire test suite was silently depending
on a `spasm.db` file left over from some earlier manual `uvicorn`
run having the right (and up to date) schema already on disk — which
is exactly why adding new columns to `DriftEvent` (for the
intent-classifier pipeline) broke every test that touched drift
events: the stale file didn't have the new columns, and deleting it
left NO tables at all, since nothing was creating them.

This fixture makes the test suite self-contained: it creates
whatever schema `app.models` currently defines, in a throwaway
`test_spasm.db`, before the first test runs — so test runs no longer
depend on some other process having created `spasm.db` first, and a
schema change (like this session's new columns) can't silently break
every test that never got a fresh database.
"""
import asyncio
import os

import pytest

# Point the app at a dedicated test database BEFORE any app module is
# imported (Settings reads the env var at import time via pydantic-settings),
# so test runs never touch a developer's real spasm.db.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_spasm.db")


@pytest.fixture(scope="session", autouse=True)
def _create_test_schema():
    from app.db.session import init_db

    asyncio.run(init_db())
    yield
    # Deliberately NOT deleting test_spasm.db after the run — leaving it
    # around lets a failed test's data be inspected, and the next run just
    # reuses/extends the same schema (create_all is a no-op on existing
    # tables). Delete it manually if you change a model's columns again.
