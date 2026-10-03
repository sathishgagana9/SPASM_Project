"""
Multi-turn stability experiment (spec section 21): measures how
persona stability evolves as conversation length grows. For each
configured turn count, runs that many filler in-scope exchanges,
then poses the multi-turn scenario's final (drift-testing) prompt,
and records stability/drift/repair-count at that point.

This directly produces the data spec section 21 asks for:
conversation_turn, persona_stability, drift_probability, repair_count.

Usage: python experiment_multiturn.py
"""
import asyncio

from common import load_config, load_jsonl, load_personas, new_experiment_id, save_results

# Generic in-scope filler prompts, reused across personas — intentionally
# bland so they don't themselves trigger drift; only pads conversation length.
FILLER_PROMPTS = [
    "Can you give me a bit more detail on that?",
    "That makes sense, what else should I know?",
    "Can you summarize what we've covered so far?",
    "Is there a simpler way to think about this?",
    "What's a common mistake people make here?",
]


async def main():
    config = load_config()
    scenarios = load_jsonl(config["dataset"]["multiturn"])
    personas = load_personas()
    turn_counts = config["multiturn_experiment"]["turn_counts"]
    experiment_id = new_experiment_id("experiment_multiturn")

    from app.drift.detector import detect_drift
    from app.providers.base import ChatMessage, ProviderError
    from app.providers.registry import get_provider
    from app.repair.engine import repair as run_repair
    from app.services.persona_compiler import compile_persona

    records = []
    for model_cfg in config["models"]:
        provider = get_provider(model_cfg["provider"])
        for scenario in scenarios:
            persona = personas.get(scenario["persona_id"])
            if persona is None:
                continue
            system_prompt = compile_persona(persona)

            for turn_count in turn_counts:
                messages = [ChatMessage(role="system", content=system_prompt)]
                repair_count = 0

                # Pad with filler exchanges up to turn_count (cycling the filler list if needed).
                for i in range(turn_count):
                    filler = FILLER_PROMPTS[i % len(FILLER_PROMPTS)]
                    messages.append(ChatMessage(role="user", content=filler))
                    try:
                        filler_result = await provider.generate(messages, model=model_cfg["model"], temperature=config["generation"]["temperature"])
                    except ProviderError:
                        break
                    messages.append(ChatMessage(role="assistant", content=filler_result.content))

                # Now the actual scenario's drift-testing prompt.
                messages.append(ChatMessage(role="user", content=scenario["final_user_prompt"]))
                try:
                    result = await provider.generate(messages, model=model_cfg["model"], temperature=config["generation"]["temperature"])
                except ProviderError as e:
                    records.append({
                        "scenario": scenario["scenario"], "persona_id": scenario["persona_id"],
                        "model_label": model_cfg["label"], "conversation_turn": turn_count,
                        "success": False, "error": {"message": str(e), "kind": e.kind},
                    })
                    continue

                history_texts = [m.content for m in messages if m.role == "assistant"]
                drift_result = detect_drift(persona, result.content, user_prompt=scenario["final_user_prompt"], history=history_texts)

                if drift_result["detected"]:
                    repair_result = await run_repair(
                        persona=persona, provider=provider, model=model_cfg["model"],
                        conversation_messages=messages, original_response=result.content, drift_event=drift_result,
                    )
                    if repair_result["success"]:
                        repair_count = 1

                records.append({
                    "scenario": scenario["scenario"],
                    "persona_id": scenario["persona_id"],
                    "model_label": model_cfg["label"],
                    "conversation_turn": turn_count,
                    "success": True,
                    "persona_stability": drift_result["overall_stability"],
                    "drift_probability": drift_result["drift_probability"],
                    "repair_count": repair_count,
                })

    save_results(experiment_id, config, records)


if __name__ == "__main__":
    asyncio.run(main())
