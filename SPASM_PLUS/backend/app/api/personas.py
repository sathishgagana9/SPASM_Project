"""
Persona CRUD API — full schema (Phase 2), plus enable/disable,
duplicate, and dashboard connection/run management.

`display_index` is assigned once at creation (max existing + 1) and
never reassigned, so a persona's generic label stays stable even if
other personas are deleted later.

`activate`/`deactivate` are kept as the "Enabled/Disabled" toggle
from the persona dashboard spec. They are intentionally NOT mutually
exclusive anymore — the dashboard needs multiple personas
enabled/connected/running at once (see the Dashboard summary:
"Connected: 3, Running: 2"), which the old single-active-persona
design didn't support.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.conversation import Conversation
from app.models.persona import Persona
from app.providers.base import ProviderError
from app.providers.registry import get_provider
from app.schemas.persona import (
    ConnectionStatus,
    PersonaConnectRequest,
    PersonaCreate,
    PersonaRead,
    PersonaUpdate,
)

router = APIRouter(prefix="/api/personas", tags=["personas"])


async def _next_display_index(db: AsyncSession) -> int:
    result = await db.execute(select(func.max(Persona.display_index)))
    current_max = result.scalar()
    return (current_max or 0) + 1


@router.get("", response_model=list[PersonaRead])
async def list_personas(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Persona).order_by(Persona.display_index))
    return result.scalars().all()


@router.post("", response_model=PersonaRead, status_code=201)
async def create_persona(payload: PersonaCreate, db: AsyncSession = Depends(get_db)):
    persona = Persona(display_index=await _next_display_index(db), **payload.model_dump())
    db.add(persona)
    await db.commit()
    await db.refresh(persona)
    return persona


@router.get("/{persona_id}", response_model=PersonaRead)
async def get_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona


@router.put("/{persona_id}", response_model=PersonaRead)
async def update_persona(persona_id: str, payload: PersonaUpdate, db: AsyncSession = Depends(get_db)):
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    for field, value in payload.model_dump().items():
        setattr(persona, field, value)
    await db.commit()
    await db.refresh(persona)
    return persona


@router.delete("/{persona_id}", status_code=204)
async def delete_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    await db.delete(persona)
    await db.commit()


@router.post("/{persona_id}/duplicate", response_model=PersonaRead, status_code=201)
async def duplicate_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    original = await db.get(Persona, persona_id)
    if not original:
        raise HTTPException(status_code=404, detail="Persona not found")
    copy = Persona(
        id=str(uuid.uuid4()),
        display_index=await _next_display_index(db),
        name=f"{original.name} (copy)",
        description=original.description,
        identity=original.identity,
        tone=original.tone,
        personality_traits=list(original.personality_traits),
        goals=list(original.goals),
        values=list(original.values),
        behavior_rules=list(original.behavior_rules),
        knowledge_boundaries=list(original.knowledge_boundaries),
        response_constraints=list(original.response_constraints),
        forbidden_behaviors=list(original.forbidden_behaviors),
        example_responses=list(original.example_responses),
        is_active=False,
        # Deliberately NOT copied: connection/run state — a duplicate starts disconnected.
    )
    db.add(copy)
    await db.commit()
    await db.refresh(copy)
    return copy


@router.post("/{persona_id}/activate", response_model=PersonaRead)
async def activate_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    """Enables this persona (dashboard 'Enabled' state). Multiple personas can be enabled at once."""
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    persona.is_active = True
    await db.commit()
    await db.refresh(persona)
    return persona


@router.post("/{persona_id}/deactivate", response_model=PersonaRead)
async def deactivate_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    persona.is_active = False
    if persona.running:
        persona.running = False  # disabling a persona stops it too
    await db.commit()
    await db.refresh(persona)
    return persona


@router.post("/{persona_id}/connect", response_model=PersonaRead)
async def connect_persona(persona_id: str, payload: PersonaConnectRequest, db: AsyncSession = Depends(get_db)):
    """
    Stores the provider/model for this persona and runs a REAL health
    check against it before marking it connected. Never marks
    'connected' on an unreachable provider — see /test-connection for
    a health check that doesn't mutate stored state.
    """
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    try:
        provider = get_provider(payload.provider)
        health = await provider.health()
    except ProviderError as e:
        persona.default_provider = payload.provider
        persona.default_model = payload.model
        persona.connected = False
        persona.last_connection_error = str(e)
        await db.commit()
        await db.refresh(persona)
        return persona

    persona.default_provider = payload.provider
    persona.default_model = payload.model
    persona.connected = health.get("status") == "connected"
    persona.last_connection_error = "" if persona.connected else f"Provider status: {health.get('status')}"
    await db.commit()
    await db.refresh(persona)
    return persona


@router.post("/{persona_id}/disconnect", response_model=PersonaRead)
async def disconnect_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    persona.connected = False
    persona.running = False  # can't run while disconnected
    await db.commit()
    await db.refresh(persona)
    return persona


@router.post("/{persona_id}/test-connection", response_model=ConnectionStatus)
async def test_connection(persona_id: str, db: AsyncSession = Depends(get_db)):
    """Live health check using the persona's stored provider config. Does not change stored state."""
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    if not persona.default_provider:
        return ConnectionStatus(connected=False, status="disconnected", error="No provider configured yet")

    try:
        provider = get_provider(persona.default_provider)
        health = await provider.health()
        connected = health.get("status") == "connected"
        return ConnectionStatus(
            connected=connected,
            status=health.get("status", "error"),
            error="" if connected else f"Provider status: {health.get('status')}",
        )
    except ProviderError as e:
        return ConnectionStatus(connected=False, status="unreachable", error=str(e))


@router.post("/{persona_id}/run", response_model=PersonaRead)
async def run_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    """
    Starts (or resumes) execution: creates a new conversation using
    the persona's connected provider/model and marks it running.
    Requires the persona to be connected first — running an
    unconnected persona is refused rather than silently no-opping.
    """
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    if not persona.connected:
        raise HTTPException(status_code=400, detail="Persona is not connected. Connect it before running.")

    convo = Conversation(
        persona_id=persona.id,
        provider=persona.default_provider,
        model=persona.default_model,
        title=f"Persona {persona.display_index} session",
    )
    db.add(convo)
    await db.flush()

    persona.running = True
    persona.active_conversation_id = convo.id
    await db.commit()
    await db.refresh(persona)
    return persona


@router.post("/{persona_id}/stop", response_model=PersonaRead)
async def stop_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    persona.running = False
    await db.commit()
    await db.refresh(persona)
    return persona
