"""
Ablation condition: persona system prompt + intent-classifier gate,
but NO repair loop and NO fused detector. Isolates what the gate
ALONE contributes, separate from repair — needed because
`experiment_full_spasm.py` bundles gate + repair + detection together,
which conflates their individual effects. Sits between
`baseline_persona_prompt.py` (prompt only) and `experiment_full_spasm.py`
(everything) in the ablation ladder documented in
docs/RESEARCH_CONTRIBUTION.md's experiment design section.

If the classifier blocks a request, the boundary response is recorded
as the final output (matching production behavior) and no post-hoc
detection/repair runs — this condition exists specifically to measure
"gate-only" performance, not to also exercise the repair path.

Usage: python experiment_classifier_gate_only.py
"""
import asyncio

from common import load_config, load_jsonl, load_personas, new_experiment_id, save_results


async def main():
    config = load_config()
    prompts = load_jsonl(config["dataset"]["prompts"])
    personas = load_personas()
    experiment_id = new_experiment_id("experiment_classifier_gate_only")

    from app.drift.boundary_response import build_boundary_response
    from app.drift.detector import detect_drift
    from app.drift.intent_classifier import classify_intent
    from app.providers.base import ChatMessage, ProviderError
    from app.providers.registry import get_provider
    from app.services.persona_compiler import compile_persona

    all_personas = list(personas.values())
    records = []
    for model_cfg in config["models"]:
        provider = get_provider(model_cfg["provider"])
        for item in prompts:
            persona = personas.get(item["persona_id"])
            if persona is None:
                continue

            classification = await classify_intent(persona, item["user_prompt"], provider, model_cfg["model"], conversation_history=[])

            if not classification.in_scope or classification.persona_switch_attempt:
                response_text = build_boundary_response(persona, classification, available_personas=all_personas)
                records.append({
                    "prompt_id": item["id"], "persona_id": item["persona_id"], "model_label": model_cfg["label"],
                    "user_prompt": item["user_prompt"], "expected_scope": item.get("expected_scope"),
                    "gate_blocked": True, "classification_method": classification.method,
                    "final_response": response_text, "final_stability": 1.0,  # correctly-enforced boundary = fully stable, per spec Part 16
                })
                continue

            system_prompt = compile_persona(persona)
            messages = [ChatMessage(role="system", content=system_prompt), ChatMessage(role="user", content=item["user_prompt"])]
            try:
                result = await provider.generate(messages, model=model_cfg["model"], temperature=config["generation"]["temperature"])
            except ProviderError as e:
                records.append({
                    "prompt_id": item["id"], "persona_id": item["persona_id"], "model_label": model_cfg["label"],
                    "gate_blocked": False, "error": {"message": str(e), "kind": e.kind},
                })
                continue

            # Gate allowed it through — still run post-hoc detection to measure
            # stability, but explicitly do NOT repair (that's what makes this
            # "gate-only" rather than "full system").
            drift_result = detect_drift(persona, result.content, user_prompt=item["user_prompt"])
            records.append({
                "prompt_id": item["id"], "persona_id": item["persona_id"], "model_label": model_cfg["label"],
                "user_prompt": item["user_prompt"], "expected_scope": item.get("expected_scope"),
                "gate_blocked": False, "classification_method": classification.method,
                "final_response": result.content, "final_stability": drift_result["overall_stability"],
                "drift_result": drift_result,
            })

    save_results(experiment_id, config, records)


if __name__ == "__main__":
    asyncio.run(main())
