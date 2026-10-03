"""
Runs the adversarial attack set (persona-switch attempts, prompt
injection, etc.) through full SPASM++ and records whether each
attack succeeded (drift occurred and wasn't repaired), was caught
but not repaired, or was fully handled.

Usage: python experiment_adversarial.py
"""
import asyncio

from common import load_config, load_jsonl, load_personas, new_experiment_id, save_results


async def main():
    config = load_config()
    attacks = load_jsonl(config["dataset"]["adversarial"])
    personas = load_personas()
    experiment_id = new_experiment_id("experiment_adversarial")

    from app.drift.detector import detect_drift
    from app.providers.base import ChatMessage, ProviderError
    from app.providers.registry import get_provider
    from app.repair.engine import repair as run_repair
    from app.services.persona_compiler import compile_persona

    records = []
    for model_cfg in config["models"]:
        provider = get_provider(model_cfg["provider"])
        for item in attacks:
            persona = personas.get(item["persona_id"])
            if persona is None:
                continue
            system_prompt = compile_persona(persona)

            # Multi-turn attacks include a conversation prefix; single-turn attacks don't.
            history_messages = [ChatMessage(role="system", content=system_prompt)]
            for turn in item.get("conversation", []):
                history_messages.append(ChatMessage(role=turn["role"], content=turn["content"]))
            history_messages.append(ChatMessage(role="user", content=item["user_prompt"]))

            try:
                result = await provider.generate(history_messages, model=model_cfg["model"], temperature=config["generation"]["temperature"])
            except ProviderError as e:
                records.append({
                    "attack_id": item["id"], "attack_type": item["attack_type"], "persona_id": item["persona_id"],
                    "model_label": model_cfg["label"], "success": False, "error": {"message": str(e), "kind": e.kind},
                })
                continue

            prior_assistant_texts = [t["content"] for t in item.get("conversation", []) if t["role"] == "assistant"]
            drift_result = detect_drift(persona, result.content, user_prompt=item["user_prompt"], history=prior_assistant_texts)

            repair_result = None
            attack_outcome = "attack_failed_no_drift_detected"  # detector saw nothing wrong
            if drift_result["detected"]:
                repair_result = await run_repair(
                    persona=persona, provider=provider, model=model_cfg["model"],
                    conversation_messages=history_messages, original_response=result.content, drift_event=drift_result,
                )
                attack_outcome = "attack_caught_and_repaired" if repair_result["success"] else "attack_caught_repair_failed"

            records.append({
                "attack_id": item["id"],
                "attack_type": item["attack_type"],
                "persona_id": item["persona_id"],
                "model_label": model_cfg["label"],
                "success": True,
                "response": result.content,
                "drift_result": drift_result,
                "repair_result": repair_result,
                "attack_outcome": attack_outcome,
                "note": item.get("note", ""),
            })

    save_results(experiment_id, config, records)


if __name__ == "__main__":
    asyncio.run(main())
