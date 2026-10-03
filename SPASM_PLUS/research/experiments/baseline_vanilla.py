"""
Baseline A: vanilla LLM, no persona system prompt at all, no drift
detection. The floor everything else is compared against.

Usage: python baseline_vanilla.py
"""
import asyncio

from common import load_config, load_jsonl, new_experiment_id, run_single_trial, save_results


async def main():
    config = load_config()
    prompts = load_jsonl(config["dataset"]["prompts"])
    experiment_id = new_experiment_id("baseline_vanilla")

    from app.providers.base import ChatMessage

    records = []
    for model_cfg in config["models"]:
        for item in prompts:
            messages = [ChatMessage(role="user", content=item["user_prompt"])]
            trial = await run_single_trial(
                model_cfg["provider"], model_cfg["model"], messages, config["generation"]["temperature"]
            )
            records.append({
                "prompt_id": item["id"],
                "persona_id": item["persona_id"],  # kept for comparability even though vanilla ignores it
                "model_label": model_cfg["label"],
                "provider": model_cfg["provider"],
                "model": model_cfg["model"],
                "user_prompt": item["user_prompt"],
                "expected_scope": item.get("expected_scope"),
                **trial,
            })

    save_results(experiment_id, config, records)


if __name__ == "__main__":
    asyncio.run(main())
