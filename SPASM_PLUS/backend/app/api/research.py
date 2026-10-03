"""
Research API — minimal working CRUD (title/topic/questions/notes/
sources/findings/summary, optionally linked to a persona/conversation).
Not the full "research mode" from the original SPASM++ spec
(StressBench/evaluation harness/experiment provenance) — those are
still NOT IMPLEMENTED, since they require running real experiments
against a live LLM. This is a working notes tool, not a placeholder.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.research import ResearchNote
from app.schemas.research import ResearchNoteCreate, ResearchNoteRead, ResearchNoteUpdate

router = APIRouter(prefix="/api/research", tags=["research"])


@router.get("", response_model=list[ResearchNoteRead])
async def list_notes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResearchNote).order_by(ResearchNote.updated_at.desc()))
    return result.scalars().all()


@router.post("", response_model=ResearchNoteRead, status_code=201)
async def create_note(payload: ResearchNoteCreate, db: AsyncSession = Depends(get_db)):
    note = ResearchNote(**payload.model_dump())
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("/{note_id}", response_model=ResearchNoteRead)
async def get_note(note_id: str, db: AsyncSession = Depends(get_db)):
    note = await db.get(ResearchNote, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Research note not found")
    return note


@router.put("/{note_id}", response_model=ResearchNoteRead)
async def update_note(note_id: str, payload: ResearchNoteUpdate, db: AsyncSession = Depends(get_db)):
    note = await db.get(ResearchNote, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Research note not found")
    for field, value in payload.model_dump().items():
        setattr(note, field, value)
    await db.commit()
    await db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: str, db: AsyncSession = Depends(get_db)):
    note = await db.get(ResearchNote, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Research note not found")
    await db.delete(note)
    await db.commit()
