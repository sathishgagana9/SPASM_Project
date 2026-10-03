"""
Conversation + Chat API — the core product loop, plus chat-history
management (rename/delete/auto-title) and a streaming endpoint.

POST /{id}/messages (non-streaming) and POST /{id}/messages/stream
(SSE) both run: generate -> detect drift -> repair if needed ->
verify -> persist. The streaming endpoint yields content tokens as
they arrive from the provider, then sends drift/repair results as
separate SSE events once available — so the user sees text
immediately and monitoring updates a moment later, per the
"generation must not block on monitoring" requirement. Drift
detection itself is fast (no LLM call, pure string processing) so it
runs synchronously right after the stream completes; only the
*repair* step (which needs another LLM call) meaningfully adds
latency, and it only runs when drift was actually detected.

## Always-persist DriftEvent (changed for turn-by-turn analysis)

Every monitored turn now gets a DriftEvent row, whether or not drift
was detected (`detected` reflects the real result either way) —
previously only detected-drift turns were persisted, which meant a
frontend "turn-by-turn analysis" view could only ever show turns that
already went wrong, with silent gaps for every stable turn. Repair
still only runs when `detected=True`, unchanged.
"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.drift.boundary_response import build_boundary_response
from app.drift.detector import detect_drift
from app.drift.intent_classifier import CLASSIFIER_VERSION, IntentClassification, classify_intent
from app.models.conversation import Conversation, Message
from app.models.drift_event import DriftEvent, RepairEvent
from app.models.persona import Persona
from app.providers.base import ChatMessage, ProviderError
from app.providers.registry import get_provider
from app.repair.engine import repair as run_repair
from app.schemas.conversation import (
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
    DriftEventRead,
    MessageRead,
    RepairEventRead,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services.persona_compiler import compile_persona

router = APIRouter(prefix="/api/conversations", tags=["conversations"])
logger = logging.getLogger("spasm.chat")

AUTO_TITLE_MAX_LEN = 48


def _auto_title(content: str) -> str:
    """Derives a short conversation title from the first user message,
    e.g. 'Explain linked lists' -> 'Explain linked lists'. Truncates
    with an ellipsis rather than cutting mid-word where possible."""
    text = " ".join(content.strip().split())
    if len(text) <= AUTO_TITLE_MAX_LEN:
        title = text
    else:
        truncated = text[:AUTO_TITLE_MAX_LEN]
        last_space = truncated.rfind(" ")
        title = (truncated[:last_space] if last_space > 20 else truncated) + "…"
    return title[0].upper() + title[1:] if title else "New conversation"


def _provider_error_response(e: ProviderError) -> HTTPException:
    status_map = {"timeout": 504, "unreachable": 502, "auth": 502, "rate_limit": 429, "malformed": 502}
    status_code = status_map.get(e.kind, 502)
    return HTTPException(status_code=status_code, detail={"message": str(e), "error_type": e.kind})


@router.post("", response_model=ConversationRead, status_code=201)
async def create_conversation(payload: ConversationCreate, db: AsyncSession = Depends(get_db)):
    persona = await db.get(Persona, payload.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    convo = Conversation(
        persona_id=payload.persona_id, provider=payload.provider, model=payload.model, title=payload.title
    )
    db.add(convo)
    await db.commit()
    await db.refresh(convo)
    return convo


@router.get("", response_model=list[ConversationRead])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conversation).order_by(Conversation.updated_at.desc()))
    return result.scalars().all()


@router.patch("/{conversation_id}", response_model=ConversationRead)
async def rename_conversation(conversation_id: str, payload: ConversationUpdate, db: AsyncSession = Depends(get_db)):
    convo = await db.get(Conversation, conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    convo.title = payload.title.strip() or convo.title
    await db.commit()
    await db.refresh(convo)
    return convo


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    convo = await db.get(Conversation, conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    # Messages cascade via the ORM relationship; drift/repair events are
    # separate tables without a relationship, so clean them up explicitly.
    await db.execute(delete(DriftEvent).where(DriftEvent.conversation_id == conversation_id))
    await db.execute(delete(RepairEvent).where(RepairEvent.conversation_id == conversation_id))
    await db.delete(convo)
    await db.commit()


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(conversation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    )
    return result.scalars().all()


@router.get("/{conversation_id}/drift-events", response_model=list[DriftEventRead])
async def list_drift_events(conversation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DriftEvent).where(DriftEvent.conversation_id == conversation_id).order_by(DriftEvent.created_at)
    )
    return result.scalars().all()


@router.get("/{conversation_id}/repair-events", response_model=list[RepairEventRead])
async def list_repair_events(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """Added for the turn-by-turn analysis pane — repair events were
    previously only ever seen live (inline in send_message's response or
    streamed as an SSE event), with no way to reload a conversation's repair
    history after a page refresh."""
    result = await db.execute(
        select(RepairEvent).where(RepairEvent.conversation_id == conversation_id).order_by(RepairEvent.created_at)
    )
    return result.scalars().all()


async def _load_context(conversation_id: str, db: AsyncSession):
    """Shared setup for both the sync and streaming send-message paths."""
    convo = await db.get(Conversation, conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    persona = await db.get(Persona, convo.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona for this conversation no longer exists")
    return convo, persona


async def _build_provider_messages(conversation_id: str, persona: Persona, db: AsyncSession) -> list[ChatMessage]:
    history_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    )
    history = history_result.scalars().all()
    system_prompt = compile_persona(persona)
    return [ChatMessage(role="system", content=system_prompt)] + [
        ChatMessage(role=m.role, content=m.content) for m in history
    ]


def _build_boundary_drift_event(conversation_id: str, message_id: str, classification: IntentClassification) -> DriftEvent:
    """Persisted when the intent-classifier pipeline BLOCKS a request before
    generation (either an out-of-scope topical request or a persona-switch
    attempt) — drift_type is 'persona_boundary_enforced' for both cases;
    persona_switch_attempt/requested_role/requested_domain (see the model's
    comment) record what the USER asked for, so the analysis panel can show
    "user attempted X, assistant correctly stayed in persona" rather than
    conflating the attempt with actual drift. overall_stability is 1.0 here
    (not 0.0, unlike the previous session's identity_guard-only version) —
    the assistant did NOT drift; it correctly refused, which is the SUCCESS
    case, not a violation, per the spec's "a correct refusal can be a
    HIGH-QUALITY response" requirement."""
    reason = (
        f"Blocked before generation: {classification.reasoning}"
        + (" (degraded fallback mode — see method)" if classification.degraded else "")
    )
    return DriftEvent(
        conversation_id=conversation_id,
        message_id=message_id,
        detected=False,  # the ASSISTANT did not drift — it was correctly prevented from answering
        drift_type="persona_boundary_enforced",
        severity="none",
        confidence=classification.confidence,
        drift_probability=0.0,
        dimensions={
            "identity": 1.0, "scope": 1.0, "behavior": 1.0, "tone": 1.0,
            "goals": 1.0, "knowledge": 1.0, "instruction": 1.0, "context": 1.0,
        },
        overall_stability=1.0,
        reason=reason,
        method=classification.method,
        detector_version=CLASSIFIER_VERSION,
        threshold_version="n/a",
        scope_classification="persona_switch_blocked" if classification.persona_switch_attempt else "out_of_scope_blocked",
        scope_similarity=None,
        context_contradictions=[],
        persona_switch_attempt=classification.persona_switch_attempt,
        requested_role=classification.requested_persona_or_role,
        requested_domain=classification.requested_domain,
    )


def _build_drift_event_row(
    conversation_id: str, message_id: str, drift_result: dict, classification: IntentClassification | None = None,
) -> DriftEvent:
    """Always called for every monitored turn now (not just when drift was
    detected) — see the module docstring's 'always-persist' note. This is
    what makes turn-by-turn analysis in the frontend possible: without a row
    for STABLE turns too, the analysis pane could only ever show the turns
    that already went wrong, never the full conversation timeline.

    `classification`, when given, is the (already-computed, already-passed)
    intent-classifier result for this turn's user message — carrying its
    `requested_domain` through even on ALLOWED turns, not just blocked ones,
    so "Question Domain" in the analysis panel reflects the actual request on
    every turn (spec Part 31/29), not just the turns that got refused."""
    return DriftEvent(
        conversation_id=conversation_id,
        message_id=message_id,
        detected=drift_result["detected"],
        drift_type=drift_result["drift_type"],
        severity=drift_result["severity"],
        confidence=drift_result["confidence"],
        drift_probability=drift_result.get("drift_probability", 0.0),
        dimensions=drift_result["dimensions"],
        overall_stability=drift_result["overall_stability"],
        reason=drift_result["reason"],
        method=drift_result["method"],
        detector_version=drift_result.get("detector_version", ""),
        threshold_version=drift_result.get("threshold_version", ""),
        scope_classification=drift_result.get("scope_classification", ""),
        scope_similarity=drift_result.get("scope_similarity"),
        context_contradictions=drift_result.get("context_contradictions", []),
        # False here is correct even when classification is provided: this
        # row only ever gets built for ALLOWED turns (blocked turns go
        # through _build_boundary_drift_event instead), and an allowed turn
        # was, by definition, not classified as a persona-switch attempt.
        persona_switch_attempt=False,
        requested_role=None,
        requested_domain=classification.requested_domain if classification else "",
    )


@router.post("/{conversation_id}/messages", response_model=SendMessageResponse)
async def send_message(conversation_id: str, payload: SendMessageRequest, db: AsyncSession = Depends(get_db)):
    convo, persona = await _load_context(conversation_id, db)

    is_first_message = (
        await db.execute(select(Message).where(Message.conversation_id == conversation_id).limit(1))
    ).scalar_one_or_none() is None

    user_msg = Message(conversation_id=conversation_id, role="user", content=payload.content)
    db.add(user_msg)
    if is_first_message and convo.title == "New conversation":
        convo.title = _auto_title(payload.content)
    await db.commit()
    await db.refresh(user_msg)

    # Application-level persona-boundary gate (app/drift/intent_classifier.py).
    # This ALWAYS runs before generation when monitoring is on — it is the
    # PRIMARY defense (semantic intent classification via the same Groq
    # provider, not keyword matching) per the "do not rely on keyword
    # blocking; evaluate actual intent, not just a system-prompt instruction"
    # requirement. The previous session's regex-only identity_guard is now
    # used ONLY internally, as this classifier's degraded-mode fallback if
    # the Groq call itself fails — see intent_classifier.py.
    if payload.monitor:
        available_personas = list((await db.execute(select(Persona))).scalars().all())
        prior_history = (await db.execute(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
        )).scalars().all()
        history_texts = [m.content for m in prior_history if m.id != user_msg.id]

        try:
            classifier_provider = get_provider(convo.provider)
        except ProviderError as e:
            raise _provider_error_response(e) from e

        classification = await classify_intent(
            persona, payload.content, classifier_provider, convo.model, conversation_history=history_texts,
        )

        if not classification.in_scope or classification.persona_switch_attempt:
            response_text = build_boundary_response(persona, classification, available_personas=available_personas)
            drift_event_row = _build_boundary_drift_event(conversation_id, user_msg.id, classification)
            db.add(drift_event_row)
            await db.commit()
            await db.refresh(drift_event_row)
            convo.stability_score = 1.0  # the boundary held — the persona stayed intact

            assistant_msg = Message(conversation_id=conversation_id, role="assistant", content=response_text, was_repaired=False)
            db.add(assistant_msg)
            await db.commit()
            await db.refresh(assistant_msg)
            await db.refresh(convo)

            return SendMessageResponse(
                user_message=MessageRead.model_validate(user_msg),
                assistant_message=MessageRead.model_validate(assistant_msg),
                drift_event=DriftEventRead.model_validate(drift_event_row),
                repair_event=None,
                conversation_stability=convo.stability_score,
            )

    provider_messages = await _build_provider_messages(conversation_id, persona, db)

    try:
        provider = get_provider(convo.provider)
        result = await provider.generate(provider_messages, model=convo.model)
    except ProviderError as e:
        raise _provider_error_response(e) from e

    response_text = result.content
    was_repaired = False
    drift_event_row = None
    repair_event_row = None

    if payload.monitor:
        drift_result = detect_drift(
            persona, response_text,
            user_prompt=payload.content,
            history=[m.content for m in provider_messages if m.role == "assistant"],
        )

        drift_event_row = _build_drift_event_row(conversation_id, user_msg.id, drift_result, classification=classification)
        db.add(drift_event_row)
        await db.commit()
        await db.refresh(drift_event_row)

        if drift_result["detected"]:
            try:
                repair_result = await run_repair(
                    persona=persona,
                    provider=provider,
                    model=convo.model,
                    conversation_messages=provider_messages,
                    original_response=response_text,
                    drift_event=drift_result,
                )
            except ProviderError:
                repair_result = {
                    "operator": "none",
                    "stability_before": drift_result["overall_stability"],
                    "stability_after": drift_result["overall_stability"],
                    "stability_improvement": 0.0,
                    "success": False,
                    "duration_ms": 0,
                    "repaired_content": "",
                    "token_overhead": 0,
                    "quality_flags": ["provider_error"],
                }

            repair_event_row = RepairEvent(
                conversation_id=conversation_id,
                drift_event_id=drift_event_row.id,
                operator=repair_result["operator"],
                stability_before=repair_result["stability_before"],
                stability_after=repair_result["stability_after"],
                stability_improvement=repair_result.get("stability_improvement", 0.0),
                success=repair_result["success"],
                duration_ms=repair_result["duration_ms"],
                repaired_content=repair_result.get("repaired_content", ""),
                token_overhead=repair_result.get("token_overhead", 0),
                quality_flags=repair_result.get("quality_flags", []),
            )
            db.add(repair_event_row)

            if repair_result["success"] and repair_result.get("repaired_content"):
                response_text = repair_result["repaired_content"]
                was_repaired = True
                convo.stability_score = repair_result["stability_after"]
            else:
                convo.stability_score = drift_result["overall_stability"]
        else:
            convo.stability_score = drift_result["overall_stability"]

    assistant_msg = Message(
        conversation_id=conversation_id, role="assistant", content=response_text, was_repaired=was_repaired
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)
    if repair_event_row:
        await db.refresh(repair_event_row)
    await db.refresh(convo)

    return SendMessageResponse(
        user_message=MessageRead.model_validate(user_msg),
        assistant_message=MessageRead.model_validate(assistant_msg),
        drift_event=DriftEventRead.model_validate(drift_event_row) if drift_event_row else None,
        repair_event=RepairEventRead.model_validate(repair_event_row) if repair_event_row else None,
        conversation_stability=convo.stability_score,
    )


@router.post("/{conversation_id}/messages/stream")
async def send_message_stream(conversation_id: str, payload: SendMessageRequest, db: AsyncSession = Depends(get_db)):
    """
    SSE stream. Event shapes (each a JSON-encoded `data:` line):
      {"type": "token", "content": "..."}                         — one per content delta
      {"type": "error", "message": "...", "error_type": "..."}    — provider failure, stream ends
      {"type": "done", "message_id": "...", "content": "..."}     — full raw response text, before repair
      {"type": "drift", ...DriftEventRead fields...}              — only sent if drift was detected
      {"type": "repair", ...RepairEventRead fields..., "repaired_content": "..."}  — only if repair ran
      {"type": "final", "content": "...", "was_repaired": bool}   — the content actually persisted/shown
    """
    convo, persona = await _load_context(conversation_id, db)

    is_first_message = (
        await db.execute(select(Message).where(Message.conversation_id == conversation_id).limit(1))
    ).scalar_one_or_none() is None

    user_msg = Message(conversation_id=conversation_id, role="user", content=payload.content)
    db.add(user_msg)
    if is_first_message and convo.title == "New conversation":
        convo.title = _auto_title(payload.content)
    await db.commit()
    await db.refresh(user_msg)

    # Application-level persona-boundary gate — same pipeline as send_message
    # above (see the comment there and app/drift/intent_classifier.py).
    # Checked before opening the SSE stream at all, so a blocked request
    # never touches the persona's own generation call.
    if payload.monitor:
        available_personas = list((await db.execute(select(Persona))).scalars().all())
        prior_history = (await db.execute(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
        )).scalars().all()
        history_texts = [m.content for m in prior_history if m.id != user_msg.id]

        try:
            classifier_provider = get_provider(convo.provider)
        except ProviderError as e:
            raise _provider_error_response(e) from e

        classification = await classify_intent(
            persona, payload.content, classifier_provider, convo.model, conversation_history=history_texts,
        )

        if not classification.in_scope or classification.persona_switch_attempt:
            response_text = build_boundary_response(persona, classification, available_personas=available_personas)
            drift_event_row = _build_boundary_drift_event(conversation_id, user_msg.id, classification)
            db.add(drift_event_row)
            await db.commit()
            await db.refresh(drift_event_row)
            convo.stability_score = 1.0
            assistant_msg = Message(conversation_id=conversation_id, role="assistant", content=response_text, was_repaired=False)
            db.add(assistant_msg)
            await db.commit()
            await db.refresh(assistant_msg)
            await db.refresh(convo)

            async def blocked_stream():
                def sse(payload_dict: dict) -> str:
                    return f"data: {json.dumps(payload_dict)}\n\n"
                yield sse({"type": "drift", **DriftEventRead.model_validate(drift_event_row).model_dump(mode="json")})
                yield sse({"type": "final", "content": response_text, "was_repaired": False, "message_id": assistant_msg.id})

            return StreamingResponse(blocked_stream(), media_type="text/event-stream")

    provider_messages = await _build_provider_messages(conversation_id, persona, db)

    try:
        provider = get_provider(convo.provider)
    except ProviderError as e:
        # Must raise a normal HTTPException here, not inside the SSE generator below —
        # once streaming starts we can no longer change the HTTP status code, so a
        # provider construction failure (e.g. missing GROQ_API_KEY) has to be caught
        # before StreamingResponse is created, or it crashes as an unhandled 500
        # instead of a clear error the frontend can parse.
        raise _provider_error_response(e) from e

    async def event_stream():
        def sse(payload_dict: dict) -> str:
            return f"data: {json.dumps(payload_dict)}\n\n"

        collected = []
        try:
            async for delta in provider.stream(provider_messages, model=convo.model):
                collected.append(delta)
                yield sse({"type": "token", "content": delta})
        except ProviderError as e:
            yield sse({"type": "error", "message": str(e), "error_type": e.kind})
            return

        response_text = "".join(collected)
        if not response_text:
            yield sse({"type": "error", "message": "Provider returned an empty response.", "error_type": "malformed"})
            return

        yield sse({"type": "done", "content": response_text})

        was_repaired = False
        final_text = response_text

        if payload.monitor:
            drift_result = detect_drift(
                persona, response_text,
                user_prompt=payload.content,
                history=[m.content for m in provider_messages if m.role == "assistant"],
            )
            drift_event_row = _build_drift_event_row(conversation_id, user_msg.id, drift_result, classification=classification)
            db.add(drift_event_row)
            await db.commit()
            await db.refresh(drift_event_row)
            yield sse({"type": "drift", **DriftEventRead.model_validate(drift_event_row).model_dump(mode="json")})

            if drift_result["detected"]:
                try:
                    repair_result = await run_repair(
                        persona=persona,
                        provider=provider,
                        model=convo.model,
                        conversation_messages=provider_messages,
                        original_response=response_text,
                        drift_event=drift_result,
                    )
                except ProviderError:
                    repair_result = {
                        "operator": "none", "stability_before": drift_result["overall_stability"],
                        "stability_after": drift_result["overall_stability"], "stability_improvement": 0.0,
                        "success": False, "duration_ms": 0, "repaired_content": "",
                        "token_overhead": 0, "quality_flags": ["provider_error"],
                    }

                repair_event_row = RepairEvent(
                    conversation_id=conversation_id,
                    drift_event_id=drift_event_row.id,
                    operator=repair_result["operator"],
                    stability_before=repair_result["stability_before"],
                    stability_after=repair_result["stability_after"],
                    stability_improvement=repair_result.get("stability_improvement", 0.0),
                    success=repair_result["success"],
                    duration_ms=repair_result["duration_ms"],
                    repaired_content=repair_result.get("repaired_content", ""),
                    token_overhead=repair_result.get("token_overhead", 0),
                    quality_flags=repair_result.get("quality_flags", []),
                )
                db.add(repair_event_row)
                await db.commit()
                await db.refresh(repair_event_row)
                yield sse({
                    "type": "repair",
                    **RepairEventRead.model_validate(repair_event_row).model_dump(mode="json"),
                    "repaired_content": repair_result.get("repaired_content", ""),
                })

                if repair_result["success"] and repair_result.get("repaired_content"):
                    final_text = repair_result["repaired_content"]
                    was_repaired = True
                    convo.stability_score = repair_result["stability_after"]
                else:
                    convo.stability_score = drift_result["overall_stability"]
            else:
                convo.stability_score = drift_result["overall_stability"]

        assistant_msg = Message(
            conversation_id=conversation_id, role="assistant", content=final_text, was_repaired=was_repaired
        )
        db.add(assistant_msg)
        await db.commit()

        yield sse({"type": "final", "content": final_text, "was_repaired": was_repaired, "message_id": assistant_msg.id})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
