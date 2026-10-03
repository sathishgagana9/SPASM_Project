"""
Unit tests for the rule-based drift detector — these run against
synthetic personas/responses, no live LLM required.
"""
from app.drift.detector import detect_drift
from app.models.persona import Persona


def _persona(**kwargs) -> Persona:
    defaults = dict(
        name="Study Mentor",
        identity="A formal, patient academic tutor",
        tone="formal and academic",
        forbidden_behaviors=["I don't know, just Google it"],
        knowledge_boundaries=["medical diagnosis"],
        goals=["help the student understand concepts deeply"],
        behavior_rules=["explain step by step"],
    )
    defaults.update(kwargs)
    return Persona(**defaults)


def test_no_drift_on_compliant_response():
    persona = _persona()
    response = (
        "Let's work through this concept step by step so you can understand it deeply. "
        "First, consider the underlying principle..."
    )
    result = detect_drift(persona, response)
    assert result["overall_stability"] > 0.85


def test_detects_forbidden_behavior():
    persona = _persona()
    response = "I don't know, just Google it."
    result = detect_drift(persona, response)
    assert result["detected"] is True
    assert result["dimensions"]["behavior"] < 1.0


def test_detects_tone_drift_on_casual_response():
    persona = _persona()
    response = "lol yeah idk, kinda hard to explain haha!!!"
    result = detect_drift(persona, response)
    assert result["dimensions"]["tone"] < 1.0


def test_detects_identity_drift_on_generic_disclaimer():
    persona = _persona()
    response = "As an AI language model, I don't have personal opinions."
    result = detect_drift(persona, response)
    assert result["dimensions"]["identity"] < 1.0


def test_severity_thresholds_are_ordered():
    persona = _persona()
    stable_result = detect_drift(persona, "Step by step, formally, we address your goal of understanding.")
    unstable_result = detect_drift(persona, "I don't know, just Google it. lol idk haha!!! As an AI language model...")
    assert stable_result["overall_stability"] >= unstable_result["overall_stability"]
