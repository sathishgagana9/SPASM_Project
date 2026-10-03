"""
Repair engine tests using a stub provider — no live LLM required.
Verifies the repair loop actually re-checks drift rather than
blindly reporting success (spec section 22).
"""
import pytest

from app.models.persona import Persona
from app.providers.base import ChatMessage, GenerationResult, LLMProvider
from app.repair.engine import repair


class StubProvider(LLMProvider):
    name = "stub"

    def __init__(self, response_text: str):
        self.response_text = response_text

    async def generate(self, messages, model, **kwargs):
        return GenerationResult(content=self.response_text, model=model, provider=self.name)

    async def list_models(self):
        return ["stub-model"]

    async def health(self):
        return {"status": "connected"}


def _persona() -> Persona:
    return Persona(
        name="Study Mentor",
        identity="A formal academic tutor",
        tone="formal and academic",
        forbidden_behaviors=["I don't know, just Google it"],
    )


@pytest.mark.asyncio
async def test_repair_reports_success_when_new_response_is_better():
    persona = _persona()
    drift_event = {
        "severity": "medium",
        "reason": "forbidden phrase used",
        "overall_stability": 0.6,
    }
    provider = StubProvider(response_text="Let's work through this formally and step by step.")
    result = await repair(
        persona=persona,
        provider=provider,
        model="stub-model",
        conversation_messages=[ChatMessage(role="user", content="help me")],
        original_response="I don't know, just Google it.",
        drift_event=drift_event,
    )
    assert result["success"] is True
    assert result["stability_after"] > result["stability_before"]


@pytest.mark.asyncio
async def test_repair_does_not_claim_success_when_still_drifted():
    persona = _persona()
    drift_event = {
        "severity": "medium",
        "reason": "forbidden phrase used",
        "overall_stability": 0.6,
    }
    # Stub still returns a non-compliant response — repair must NOT claim success
    provider = StubProvider(response_text="I don't know, just Google it.")
    result = await repair(
        persona=persona,
        provider=provider,
        model="stub-model",
        conversation_messages=[ChatMessage(role="user", content="help me")],
        original_response="I don't know, just Google it.",
        drift_event=drift_event,
    )
    assert result["success"] is False
