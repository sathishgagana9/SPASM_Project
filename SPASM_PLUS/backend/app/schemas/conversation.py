from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class ConversationCreate(BaseModel):
    persona_id: str
    provider: str = "groq"
    model: str
    title: str = "New conversation"


class ConversationUpdate(BaseModel):
    title: str


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    role: str
    content: str
    was_repaired: bool
    created_at: datetime


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    persona_id: str
    provider: str
    model: str
    title: str
    stability_score: float
    created_at: datetime
    updated_at: datetime


class SendMessageRequest(BaseModel):
    content: str
    monitor: bool = True  # set false to skip drift detection/repair for this turn (Settings > Monitoring)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, v: str) -> str:
        # Spec Part 43: fail safely without crashing — reject an empty/
        # whitespace-only message with a clean 422 at the API boundary,
        # rather than letting it reach the intent classifier (which would
        # build a prompt asking it to classify "", a genuinely undefined
        # case) or the provider (a wasted, meaningless generation call).
        if not v.strip():
            raise ValueError("Message content cannot be empty or whitespace-only.")
        return v


class DriftEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    message_id: str
    detected: bool
    drift_type: str
    severity: str
    confidence: float
    drift_probability: float
    dimensions: dict
    overall_stability: float
    reason: str
    method: str
    detector_version: str
    threshold_version: str
    scope_classification: str
    scope_similarity: float | None
    context_contradictions: list
    persona_switch_attempt: bool
    requested_role: str | None
    requested_domain: str
    created_at: datetime


class RepairEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    drift_event_id: str
    operator: str
    stability_before: float
    stability_after: float
    stability_improvement: float
    success: bool
    duration_ms: int
    token_overhead: int
    quality_flags: list
    created_at: datetime


class SendMessageResponse(BaseModel):
    user_message: MessageRead
    assistant_message: MessageRead
    drift_event: DriftEventRead | None
    repair_event: RepairEventRead | None
    conversation_stability: float
