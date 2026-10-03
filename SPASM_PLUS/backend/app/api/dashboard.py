"""
Dashboard summary API — aggregates real persona/provider state.
Counts come directly from the personas table; nothing here is
computed by re-checking live provider health on every request (that
would make the dashboard slow/flaky) — connection status is the
last real check recorded by /connect or /test-connection.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models.persona import Persona

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Persona))
    personas = result.scalars().all()
    settings = get_settings()

    available_providers = ["groq"] if settings.groq_api_key else []

    return {
        "total_personas": len(personas),
        "connected": sum(1 for p in personas if p.connected),
        "running": sum(1 for p in personas if p.running),
        "errors": sum(1 for p in personas if p.last_connection_error and not p.connected),
        "available_providers": available_providers,
    }
