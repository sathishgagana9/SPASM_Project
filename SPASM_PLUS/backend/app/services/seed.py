"""
Built-in persona seeding — shared by the startup hook (auto-seed on
first run) and scripts/seed_personas.py (manual re-run). Idempotent:
skips any persona whose name already exists.
"""
import json
import logging
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.persona import Persona

logger = logging.getLogger("spasm.seed")
SEED_FILE = Path(__file__).resolve().parent.parent / "seed_data" / "personas.json"


async def seed_builtin_personas(db: AsyncSession) -> tuple[int, int]:
    personas = json.loads(SEED_FILE.read_text())
    created, skipped = 0, 0

    for p in personas:
        existing = await db.execute(select(Persona).where(Persona.name == p["name"]))
        if existing.scalar_one_or_none():
            skipped += 1
            continue
        max_index = (await db.execute(select(func.max(Persona.display_index)))).scalar() or 0
        db.add(Persona(display_index=max_index + 1, **p))
        created += 1

    await db.commit()
    if created:
        logger.info("Seeded %d built-in personas (%d already present)", created, skipped)
    return created, skipped
