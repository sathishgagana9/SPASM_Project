# Persona System (Phase 2)

Full schema (`backend/app/models/persona.py`): name, description,
identity, tone, personality_traits, goals, values, behavior_rules,
knowledge_boundaries, response_constraints, forbidden_behaviors,
example_responses. List fields are JSON columns.

`backend/app/services/persona_compiler.py` is the single place that
turns a `Persona` into (a) the system prompt used for generation and
(b) the structured summary the drift detector checks against — kept
in one function so "what the model was told to be" and "what the
detector expects" can't drift apart from each other.

Only one persona can be `is_active` at a time — activating one
deactivates any other (see `POST /api/personas/{id}/activate`).
