"""
Focused repair-only experiment: runs prompts through generation +
detection, and for every drift event, records before/after stability,
operator used, success, latency, and token overhead — the data
needed for the "Repair Analysis" metrics (spec section 11, 17), AND
now the full `drift_event` per record, needed as training context for
`train_repair_policy.py`'s learned bandit (see policy.py) — v2 of this
script omitted that field, which is why the trainer warns and skips
records that don't have it.

Set `--policy learned` to use `HybridPolicy` (LinUCB bandit, cold-start
via the lookup table) instead of the v2 fixed lookup table — pass
`--policy-weights <path>` to load a policy already trained by
`train_repair_policy.py`; otherwise it starts cold and warms up during
this run itself (see policy.py's HybridPolicy.warmup_updates).

Usage:
    python experiment_repair.py
    python experiment_repair.py --policy learned --policy-weights ../evaluation/policy.json
"""
import argparse
import asyncio

from common import load_config, load_jsonl, load_personas, new_experiment_id, save_results


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", choices=["lookup", "learned"], default="lookup")
    parser.add_argument("--policy-weights", type=str, default=None)
    parser.add_argument("--max-cycles", type=int, default=3)
    args = parser.parse_args()

    config = load_config()
    prompts = load_jsonl(config["dataset"]["prompts"])
    personas = load_personas()
    experiment_id = new_experiment_id(f"experiment_repair_{args.policy}")

    from app.drift.detector import detect_drift
    from app.providers.base import ChatMessage, ProviderError
    from app.providers.registry import get_provider
    from app.repair.engine import repair_until_verified
    from app.services.persona_compiler import compile_persona

    policy = None
    if args.policy == "learned":
        from app.repair.policy import HybridPolicy, LinUCBPolicy
        bandit = LinUCBPolicy.load(args.policy_weights) if args.policy_weights else LinUCBPolicy()
        policy = HybridPolicy(bandit=bandit)

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
            except ProviderError:
                continue

            drift_result = detect_drift(persona, result.content, user_prompt=item["user_prompt"])
            if not drift_result["detected"]:
                continue  # nothing to repair — not a repair-experiment data point

            repair_result = await repair_until_verified(
                persona=persona, provider=provider, model=model_cfg["model"],
                conversation_messages=messages, original_response=result.content, drift_event=drift_result,
                max_cycles=args.max_cycles, policy=policy,
            )

            records.append({
                "prompt_id": item["id"],
                "persona_id": item["persona_id"],
                "model_label": model_cfg["label"],
                "policy": args.policy,
                "operator": repair_result["operator"],
                "cycles_used": repair_result.get("cycles_used"),
                "stability_before": repair_result["stability_before"],
                "stability_after": repair_result["stability_after"],
                "stability_improvement": repair_result["stability_improvement"],
                "success": repair_result["success"],
                "duration_ms": repair_result["duration_ms"],
                "token_overhead": repair_result["token_overhead"],
                "quality_flags": repair_result["quality_flags"],
                "drift_event": drift_result,  # training context for train_repair_policy.py
            })

    save_results(experiment_id, config, records)


if __name__ == "__main__":
    asyncio.run(main())
