from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResearchNoteBase(BaseModel):
    title: str = "Untitled research"
    topic: str = ""
    questions: list[str] = []
    notes: str = ""
    sources: list[str] = []
    findings: str = ""
    summary: str = ""
    persona_id: str | None = None
    conversation_id: str | None = None


class ResearchNoteCreate(ResearchNoteBase):
    pass


class ResearchNoteUpdate(ResearchNoteBase):
    pass


class ResearchNoteRead(ResearchNoteBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime
