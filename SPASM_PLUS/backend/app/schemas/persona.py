"""
Pydantic schemas for the full Persona API.

`PersonaRead.display_label` is the server-authoritative generic
label ("Persona {display_index}") — the frontend renders this
instead of `name` everywhere a persona identity is shown. `name`
stays in the payload because the Persona Studio "Advanced Settings"
still needs to let the user edit it (it drives the actual system
prompt), but nothing in the dashboard/chat/logs UI should bind to it.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field


class PersonaBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    identity: str = ""
    tone: str = ""
    scope: str = ""
    personality_traits: list[str] = []
    goals: list[str] = []
    values: list[str] = []
    behavior_rules: list[str] = []
    knowledge_boundaries: list[str] = []
    response_constraints: list[str] = []
    forbidden_behaviors: list[str] = []
    example_responses: list[str] = []


class PersonaCreate(PersonaBase):
    pass


class PersonaUpdate(PersonaBase):
    pass


class PersonaRead(PersonaBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_index: int
    is_active: bool
    default_provider: str
    default_model: str
    connected: bool
    running: bool
    active_conversation_id: str | None
    last_connection_error: str
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def display_label(self) -> str:
        return f"Persona {self.display_index}"


class PersonaConnectRequest(BaseModel):
    provider: str
    model: str = Field(min_length=1)


class ConnectionStatus(BaseModel):
    connected: bool
    status: str  # "connected" | "error" | "unreachable"
    error: str = ""
