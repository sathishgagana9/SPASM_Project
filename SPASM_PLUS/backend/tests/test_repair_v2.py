"""
Tests for the v2 repair engine: scope_reinforcement operator
selection, escalation on multiple simultaneous violations, and the
richer verification criteria (meaningful improvement, no new severe
violation, usefulness heuristic) — not just "did stability go up".
"""
import pytest

from app.models.persona import Persona
from app.providers.base import ChatMessage, GenerationResult, LLMProvider
from app.repair.engine import repair, select_repair_operator


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
    return Persona(name="Teacher", identity="An academic tutor", scope="Academic education and study guidance")


def test_scope_violation_selects_scope_reinforcement_operator():
    drift_event = {
        "severity": "medium",
        "scope_classification": "out_of_scope_violation",
        "dimensions": {"scope": 0.15, "identity": 1.0, "behavior": 1.0, "tone": 1.0,
                        "goals": 1.0, "knowledge": 1.0, "instruction": 1.0, "context": 1.0},
    }
    assert select_repair_operator(drift_event) == "scope_reinforcement"


def test_multiple_violations_escalate_beyond_base_severity():
    drift_event = {
        "severity": "low",  # would normally be the lightest operator
        "scope_classification": "in_scope",
        "dimensions": {"scope": 1.0, "identity": 0.5, "behavior": 0.4, "tone": 0.5,
                        "goals": 1.0, "knowledge": 1.0, "instruction": 1.0, "context": 1.0},
    }
    operator = select_repair_operator(drift_event)
    assert operator != "context_reinforcement"  # escalated past the raw "low" mapping


@pytest.mark.asyncio
async def test_verification_fails_on_identical_repaired_response():
    persona = _persona()
    original = "First fry the onions, then add spices."
    provider = StubProvider(response_text=original)  # provider returns the SAME drifted response again
    drift_event = {
        "severity": "medium", "reason": "scope violation", "overall_stability": 0.6,
        "dimensions": {"scope": 0.15}, "scope_classification": "out_of_scope_violation",
    }
    result = await repair(
        persona=persona, provider=provider, model="stub-model",
        conversation_messages=[ChatMessage(role="user", content="how to make biryani")],
        original_response=original, drift_event=drift_event,
    )
    assert result["success"] is False
    assert "repaired_response_identical_to_original" in result["quality_flags"]


@pytest.mark.asyncio
async def test_verification_fails_on_degenerate_short_response():
    persona = _persona()
    provider = StubProvider(response_text="OK.")
    drift_event = {
        "severity": "medium", "reason": "drift", "overall_stability": 0.6,
        "dimensions": {}, "scope_classification": "in_scope",
    }
    result = await repair(
        persona=persona, provider=provider, model="stub-model",
        conversation_messages=[ChatMessage(role="user", content="explain linked lists in detail please")],
        original_response="Let's walk through how linked lists work, starting with nodes and pointers.",
        drift_event=drift_event,
    )
    assert result["success"] is False
    assert "repaired_response_much_shorter_than_original" in result["quality_flags"]


@pytest.mark.asyncio
async def test_successful_repair_reports_stability_improvement():
    persona = _persona()
    provider = StubProvider(
        response_text="As a teacher, that's outside my academic scope — please try a Chef persona instead."
    )
    drift_event = {
        "severity": "medium", "reason": "scope violation", "overall_stability": 0.6,
        "dimensions": {"scope": 0.15}, "scope_classification": "out_of_scope_violation",
    }
    result = await repair(
        persona=persona, provider=provider, model="stub-model",
        conversation_messages=[ChatMessage(role="user", content="how to make biryani")],
        original_response="First fry the onions, then add spices.",
        drift_event=drift_event,
    )
    assert result["stability_improvement"] > 0
    assert "quality_flags" in result
