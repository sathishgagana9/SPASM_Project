"""
Baseline C: persona prompt + drift detection, NO repair. Measures
detection alone — how often drift happens and whether the detector
catches it, without the confound of repair changing the response.

Usage: python baseline_detector.py
"""
import asyncio

from common import load_config, load_jsonl, load_personas, new_experiment_id, run_single_trial, save_results


async def main():
    config = load_config()
    prompts = load_jsonl(config["dataset"]["prompts"])
    personas = load_personas()
    experiment_id = new_experiment_id("baseline_detector")

    from app.drift.detector import detect_drift
    from app.providers.base import ChatMessage
    from app.services.persona_compiler import compile_persona

    records = []
    for model_cfg in config["models"]:
        for item in prompts:
            persona = personas.get(item["persona_id"])
            if persona is None:
                continue
            system_prompt = compile_persona(persona)
            messages = [ChatMessage(role="system", content=system_prompt), ChatMessage(role="user", content=item["user_prompt"])]
            trial = await run_single_trial(
                model_cfg["provider"], model_cfg["model"], messages, config["generation"]["temperature"]
            )

            drift_result = None
            if trial["success"]:
                drift_result = detect_drift(persona, trial["content"], user_prompt=item["user_prompt"])

            records.append({
                "prompt_id": item["id"],
                "persona_id": item["persona_id"],
                "model_label": model_cfg["label"],
                "provider": model_cfg["provider"],
                "model": model_cfg["model"],
                "user_prompt": item["user_prompt"],
                "expected_scope": item.get("expected_scope"),
                "expected_drift": item.get("expected_drift"),
                **trial,
                "drift_result": drift_result,
            })

    save_results(experiment_id, config, records)


if __name__ == "__main__":
    asyncio.run(main())
