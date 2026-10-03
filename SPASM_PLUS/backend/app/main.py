"""
SPASM++ backend entrypoint.

Phases 0-7: app wiring, CORS, DB init, health checks, full Persona
CRUD, provider abstraction (Groq only — Ollama support was removed
entirely), chat with the core drift-detect -> repair -> verify loop.
Evaluation/StressBench/Model Arena routers are NOT IMPLEMENTED yet
(app/evaluation is still an empty package) — those require running
real experiments against a live provider, which this build doesn't
fabricate.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, personas, conversations, providers as providers_api, dashboard, research, experiments
from app.core.config import get_settings
from app.db.session import init_db, AsyncSessionLocal
from app.services.seed import seed_builtin_personas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spasm")

settings = get_settings()

app = FastAPI(title="SPASM++ API", version="0.0.1-phase7")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(personas.router)
app.include_router(conversations.router)
app.include_router(providers_api.router)
app.include_router(dashboard.router)
app.include_router(research.router)
app.include_router(experiments.router)


@app.on_event("startup")
async def on_startup():
    logger.info("Starting SPASM++ backend (environment=%s)", settings.environment)
    await init_db()
    async with AsyncSessionLocal() as db:
        created, skipped = await seed_builtin_personas(db)
        if created:
            logger.info("Auto-seeded %d built-in personas on first run", created)


@app.get("/")
async def root():
    return {"name": "SPASM++ API", "phase": "0-7 - core product loop", "docs": "/docs"}
