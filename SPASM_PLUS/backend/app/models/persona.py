"""
Persona ORM model — full schema (Phase 2) + dashboard connection/run
state (added for the Persona Dashboard).

List/dict fields are stored as JSON columns. SQLite supports this
natively via SQLAlchemy's JSON type; switching to Postgres later
gets a real JSONB column for free with no model changes.

`name` remains the internal identity used by the persona prompt
compiler — it is intentionally never sent to the frontend for
display purposes (see PersonaRead.display_label in schemas/persona.py).
`display_index` is assigned once at creation and never reassigned,
so "Persona 3" always refers to the same record even if other
personas are later deleted.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Boolean, DateTime, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    display_index: Mapped[int] = mapped_column(Integer, default=0)  # assigned at creation, stable, never reused

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    identity: Mapped[str] = mapped_column(Text, default="")
    tone: Mapped[str] = mapped_column(String(120), default="")
    scope: Mapped[str] = mapped_column(Text, default="")  # what topics this persona covers (enforced by the compiler)

    personality_traits: Mapped[list] = mapped_column(JSON, default=list)
    goals: Mapped[list] = mapped_column(JSON, default=list)
    values: Mapped[list] = mapped_column(JSON, default=list)
    behavior_rules: Mapped[list] = mapped_column(JSON, default=list)
    knowledge_boundaries: Mapped[list] = mapped_column(JSON, default=list)
    response_constraints: Mapped[list] = mapped_column(JSON, default=list)
    forbidden_behaviors: Mapped[list] = mapped_column(JSON, default=list)
    example_responses: Mapped[list] = mapped_column(JSON, default=list)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)  # "Enabled" in the dashboard

    # --- Dashboard connection/run state ---
    default_provider: Mapped[str] = mapped_column(String(50), default="")
    default_model: Mapped[str] = mapped_column(String(120), default="")
    connected: Mapped[bool] = mapped_column(Boolean, default=False)  # set by /connect after a real health check
    running: Mapped[bool] = mapped_column(Boolean, default=False)
    active_conversation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    last_connection_error: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
