"""
Tests for docs/repair-engine-guarantees.md's two claims:
Property 1 (no-worse-off) and Property 2 (bounded regeneration),
plus that repair_until_verified() actually uses a HybridPolicy when given one.
"""
import pytest

from app.models.persona import Persona
from app.providers.base import GenerationResult, LLMProvider
from app.repair.engine import repair_until_verified
from app.repair.policy import HybridPolicy, LinUCBPolicy


class AlwaysWorseProvider(LLMProvider):
    """Every repair attempt returns a response that scores WORSE than the
    original — the adversarial case for Property 1. Requires a persona with
    forbidden_behaviors=["cannot help with that"] (see _persona()) so the
    detector actually scores it below stability_before, rather than relying
    on the detector's crude heuristics to happen to agree it's bad."""
    name = "stub"

    async def generate(self, messages, model, **kwargs):
        return GenerationResult(
            content="I am an AI language model and cannot help with that.", model=model, provider=self.name
        )

    async def stream(self, messages, model, **kwargs):
        result = await self.generate(messages, model, **kwargs)
        yield result.content

    async def list_models(self):
        return ["stub-model"]

    async def health(self):
        return {"status": "connected"}


class EventuallySucceedsProvider(LLMProvider):
    """Returns a bad response on the first N calls, then a clean one — tests
    that the loop actually retries and eventually returns the improved one."""
    name = "stub"

    def __init__(self, n_bad_calls: int, good_response: str, bad_response: str):
        self.n_bad_calls = n_bad_calls
        self.good_response = good_response
        self.bad_response = bad_response
        self.calls = 0

    async def generate(self, messages, model, **kwargs):
        self.calls += 1
        content = self.bad_response if self.calls <= self.n_bad_calls else self.good_response
        return GenerationResult(content=content, model=model, provider=self.name)

    async def stream(self, messages, model, **kwargs):
        result = await self.generate(messages, model, **kwargs)
        yield result.content

    async def list_models(self):
        return ["stub-model"]

    async def health(self):
        return {"status": "connected"}


def _persona(forbidden_behaviors: list[str] | None = None) -> Persona:
    return Persona(
        name="Teacher", identity="An academic tutor", scope="Academic education and study guidance",
        tone="formal, academic", forbidden_behaviors=forbidden_behaviors or [], goals=[], knowledge_boundaries=[],
        behavior_rules=[], response_constraints=[],
    )


def _drift_event(stability: float = 0.4) -> dict:
    return {
        "severity": "high",
        "overall_stability": stability,
        "scope_classification": "in_scope",
        "reason": "tone drifted casual",
        "dimensions": {"scope": 1.0, "identity": 1.0, "behavior": 1.0, "tone": 0.3,
                        "goals": 1.0, "knowledge": 1.0, "instruction": 1.0, "context": 1.0},
    }


@pytest.mark.asyncio
async def test_no_worse_off_even_when_every_attempt_is_worse():
    """Property 1: if no attempt beats the original, the returned
    stability_after must equal stability_before (never regress below it)."""
    persona = _persona(forbidden_behaviors=["cannot help with that"])
    # High stability_before (0.95) so the repaired response — which trips the
    # forbidden-behavior AND AI-disclaimer rules, scoring ~0.89 — is a genuine
    # regression the detector agrees is worse, not just an arbitrary number.
    drift_event = _drift_event(stability=0.95)
    provider = AlwaysWorseProvider()
    conversation_messages = []

    result = await repair_until_verified(
        persona=persona, provider=provider, model="stub-model",
        conversation_messages=conversation_messages, original_response="A formal, correct explanation.",
        drift_event=drift_event, max_cycles=3,
    )

    assert result["stability_after"] >= result["stability_before"]
    assert result["success"] is False
    assert result["repaired_content"] == "A formal, correct explanation."  # fell back to the original


@pytest.mark.asyncio
async def test_bounded_by_max_cycles():
    """Property 2: never more than max_cycles repair() calls (LLM generations)."""
    persona = _persona()
    drift_event = _drift_event(stability=0.4)
    provider = AlwaysWorseProvider()

    max_cycles = 2
    result = await repair_until_verified(
        persona=persona, provider=provider, model="stub-model",
        conversation_messages=[], original_response="A formal, correct explanation.",
        drift_event=drift_event, max_cycles=max_cycles,
    )
    assert result["cycles_used"] <= max_cycles


@pytest.mark.asyncio
async def test_retries_and_recovers_within_bound():
    """A provider that fails once then succeeds should be retried and the
    successful attempt returned — this is what the v2 single-shot repair()
    could never do."""
    persona = _persona()
    # stability_before is set close to (but below) what the mediocre first
    # attempt scores (~0.95, since the crude detector only mildly penalizes
    # casual tone) so that attempt correctly FAILS "meaningful improvement"
    # and triggers a retry, while the clean second attempt (~1.0) clears it.
    drift_event = _drift_event(stability=0.93)
    provider = EventuallySucceedsProvider(
        n_bad_calls=1,
        bad_response="yeah so basically it's kinda like this lol",
        good_response="This concept can be explained formally as follows: it functions through structured, well-defined rules.",
    )

    result = await repair_until_verified(
        persona=persona, provider=provider, model="stub-model",
        conversation_messages=[], original_response="I am an AI language model and cannot help with that.",
        drift_event=drift_event, max_cycles=3,
    )
    assert provider.calls >= 2
    assert result["stability_after"] >= result["stability_before"]
    assert result["success"] is True


@pytest.mark.asyncio
async def test_hybrid_policy_cold_start_matches_lookup_table():
    """With zero prior updates, HybridPolicy should behave identically to the
    v2 lookup table (select_repair_operator) — the learned policy must not
    silently take over before it has any data."""
    from app.repair.engine import select_repair_operator

    persona = _persona()
    drift_event = _drift_event(stability=0.4)
    provider = AlwaysWorseProvider()
    policy = HybridPolicy(bandit=LinUCBPolicy(), warmup_updates=50)

    result = await repair_until_verified(
        persona=persona, provider=provider, model="stub-model",
        conversation_messages=[], original_response="A formal, correct explanation.",
        drift_event=drift_event, max_cycles=1, policy=policy,
    )
    assert result["operator"] == select_repair_operator(drift_event)
