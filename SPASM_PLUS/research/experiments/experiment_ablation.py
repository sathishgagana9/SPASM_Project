"""
Ablation study: full SPASM++ minus one component at a time, to see
which components actually contribute (spec section 22).

Ablations implemented:
  - no_scope_dimension:      scope dimension weight set to 0
  - no_context_dimension:    context dimension weight set to 0
  - no_repair:                drift is detected but never repaired
  - equal_weights (control):  the current default — included so the
                               "ablated" runs are compared against the
                               exact same baseline condition

NOT implemented as a real ablation: "no semantic scoring" — since
the default semantic backend is already the lexical fallback (no
separate "semantic vs not" toggle exists at runtime beyond backend
choice), this ablation is represented by comparing
SPASM_SEMANTIC_BACKEND=lexical vs =embeddings runs instead, which
requires the optional embeddings dependency — see README note.

Usage: python experiment_ablation.py
"""
import asyncio

from common import load_config, load_jsonl, load_personas, new_experiment_id, save_results

ABLATIONS = {
    "full_spasm": {},  # no ablation — the control condition
    "no_scope_dimension": {"scope": 0.0},
    "no_context_dimension": {"context": 0.0},
}


def _weights_for_ablation(zeroed: dict) -> dict | None:
    if not zeroed:
        return None  # None = use detector's default equal weights
    from app.drift.scoring import DIMENSIONS
    weights = {d: 1.0 for d in DIMENSIONS}
    for dim, w in zeroed.items():
        weights[dim] = w
    total = sum(weights.values())
    return {d: w / total for d, w in weights.items()}


async def main():
    config = load_config()
    prompts = load_jsonl(config["dataset"]["prompts"])
    personas = load_personas()
    experiment_id = new_experiment_id("experiment_ablation")

    from app.drift.detector import detect_drift
    from app.providers.base import ChatMessage, ProviderError
    from app.providers.registry import get_provider
    from app.repair.engine import repair as run_repair
    from app.services.persona_compiler import compile_persona

    records = []
    for model_cfg in config["models"]:
        provider = get_provider(model_cfg["provider"])
        for item in prompts:
            persona = personas.get(item["persona_id"])
            if persona is None:
                continue
            system_prompt = compile_persona(persona)
            messages = [ChatMessage(role="system", content=system_prompt), ChatMessage(role="user", content=item["user_prompt"])]

            try:
                result = await provider.generate(messages, model=model_cfg["model"], temperature=config["generation"]["temperature"])
            except ProviderError as e:
                continue  # skip prompts that fail generation entirely — not informative for an ablation

            # Run the SAME generated response through each ablation condition — isolates the
            # detector/repair variable instead of confounding it with generation variance.
            for ablation_name, zeroed_dims in ABLATIONS.items():
                weights = _weights_for_ablation(zeroed_dims)
                drift_result = detect_drift(persona, result.content, user_prompt=item["user_prompt"], weights=weights)

                repair_result = None
                if drift_result["detected"] and ablation_name != "no_repair":
                    repair_result = await run_repair(
                        persona=persona, provider=provider, model=model_cfg["model"],
                        conversation_messages=messages, original_response=result.content, drift_event=drift_result,
                    )

                records.append({
                    "prompt_id": item["id"],
                    "persona_id": item["persona_id"],
                    "model_label": model_cfg["label"],
                    "ablation": ablation_name,
                    "expected_drift": item.get("expected_drift"),
                    "drift_result": drift_result,
                    "repair_result": repair_result,
                })

            # A separate no_repair condition using the default (unablated) weights
            drift_result = detect_drift(persona, result.content, user_prompt=item["user_prompt"])
            records.append({
                "prompt_id": item["id"], "persona_id": item["persona_id"], "model_label": model_cfg["label"],
                "ablation": "no_repair", "expected_drift": item.get("expected_drift"),
                "drift_result": drift_result, "repair_result": None,
            })

    save_results(experiment_id, config, records)


if __name__ == "__main__":
    asyncio.run(main())
