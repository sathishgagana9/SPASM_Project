"""
Manual re-seed of built-in personas (the backend now auto-seeds these
on first startup — this script is for re-running it explicitly, e.g.
after deleting spasm.db, or to pick up changes to personas.json
without restarting the server).

Usage (from backend/, with your venv active):

    python scripts/seed_personas.py

Safe to run more than once — skips any persona whose name already exists.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import AsyncSessionLocal, init_db
from app.services.seed import seed_builtin_personas


async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        created, skipped = await seed_builtin_personas(db)
    print(f"Created {created}, skipped {skipped} (already present).")


if __name__ == "__main__":
    asyncio.run(main())
