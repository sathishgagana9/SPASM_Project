"""
Tests for the persona compiler's scope-enforcement instructions.
This only verifies the COMPILED PROMPT contains the right
instructions — it cannot verify the LLM actually follows them
(that's a live-model behavioral question, see docs/persona-system.md).
"""
from app.models.persona import Persona
from app.services.persona_compiler import compile_persona


def test_compiler_includes_scope_instructions_when_scope_set():
    persona = Persona(name="Teacher", scope="Academic education and study guidance")
    prompt = compile_persona(persona)
    assert "SCOPE" in prompt
    assert "Academic education and study guidance" in prompt
    assert "outside your role as Teacher" in prompt or "Teacher" in prompt
    assert "do NOT answer it as a generic assistant" in prompt


def test_compiler_omits_scope_section_when_scope_empty():
    persona = Persona(name="Generic Assistant", scope="")
    prompt = compile_persona(persona)
    assert "SCOPE" not in prompt
