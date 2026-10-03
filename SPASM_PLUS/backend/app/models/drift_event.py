"""DriftEvent + RepairEvent ORM models (Phases 4-7)."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DriftEvent(Base):
    __tablename__ = "drift_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"))
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("messages.id"))
    detected: Mapped[bool] = mapped_column(Boolean, default=False)
    drift_type: Mapped[str] = mapped_column(String(50), default="none")
    severity: Mapped[str] = mapped_column(String(20), default="low")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    drift_probability: Mapped[float] = mapped_column(Float, default=0.0)  # uncalibrated — see scoring.py
    dimensions: Mapped[dict] = mapped_column(JSON, default=dict)
    overall_stability: Mapped[float] = mapped_column(Float, default=1.0)
    reason: Mapped[str] = mapped_column(Text, default="")
    method: Mapped[str] = mapped_column(String(30), default="rule_based")  # rule_based | llm_assisted
    detector_version: Mapped[str] = mapped_column(String(50), default="")
    threshold_version: Mapped[str] = mapped_column(String(50), default="")
    scope_classification: Mapped[str] = mapped_column(String(30), default="")
    scope_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    context_contradictions: Mapped[list] = mapped_column(JSON, default=list)
    # Added for the intent-classifier / persona-boundary-enforcement pipeline
    # (app/drift/intent_classifier.py) — these capture what the USER'S
    # REQUEST was asking for, independent of whether the assistant complied,
    # which is what lets the analysis panel distinguish "user attempted a
    # persona switch but the assistant correctly refused" from "the assistant
    # actually drifted" (two very different events that both used to collapse
    # into the same drift_type). persona_switch_attempt/requested_role
    # describe the USER's message; drift_type/detected/severity below
    # continue to describe the ASSISTANT's actual behavior.
    persona_switch_attempt: Mapped[bool] = mapped_column(Boolean, default=False)
    requested_role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    requested_domain: Mapped[str] = mapped_column(String(120), default="")
    evaluation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # links to a research experiment run, if any
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class RepairEvent(Base):
    __tablename__ = "repair_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"))
    drift_event_id: Mapped[str] = mapped_column(String(36), ForeignKey("drift_events.id"))
    operator: Mapped[str] = mapped_column(String(50))
    stability_before: Mapped[float] = mapped_column(Float)
    stability_after: Mapped[float] = mapped_column(Float)
    stability_improvement: Mapped[float] = mapped_column(Float, default=0.0)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    duration_ms: Mapped[int] = mapped_column(default=0)
    repaired_content: Mapped[str] = mapped_column(Text, default="")
    token_overhead: Mapped[int] = mapped_column(default=0)  # crude estimate: word-count delta, not a real tokenizer
    quality_flags: Mapped[list] = mapped_column(JSON, default=list)
    evaluation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
