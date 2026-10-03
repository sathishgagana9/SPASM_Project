"""
Full SPASM++: persona compiler + drift detection + adaptive repair +
verification. This is the proposed method in the baseline comparison
(spec section 15). v3: uses `repair_until_verified()` (bounded
retry loop with the no-worse-off guarantee, docs/repair-engine-guarantees.md)
instead of v2's single-shot `repair()` — pass `--policy learned` to
use the LinUCB bandit (policy.py) instead of the lookup table.

Usage:
    python experiment_full_spasm.py
    python experiment_full_spasm.py --policy learned --policy-weights ../evaluation/policy.json
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
    experiment_id = new_experiment_id(f"experiment_full_spasm_{args.policy}")

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
            except ProviderError as e:
                records.append({
                    "prompt_id": item["id"], "persona_id": item["persona_id"], "model_label": model_cfg["label"],
                    "success": False, "error": {"message": str(e), "kind": e.kind},
                })
                continue

            drift_result = detect_drift(persona, result.content, user_prompt=item["user_prompt"])
            repair_result = None
            final_content = result.content
            final_stability = drift_result["overall_stability"]

            if drift_result["detected"]:
                repair_result = await repair_until_verified(
                    persona=persona, provider=provider, model=model_cfg["model"],
                    conversation_messages=messages, original_response=result.content, drift_event=drift_result,
                    max_cycles=args.max_cycles, policy=policy,
                )
                final_content = repair_result["repaired_content"]  # no-worse-off guarantee (see docs/) — always >= original
                final_stability = repair_result["stability_after"]

            records.append({
                "prompt_id": item["id"],
                "persona_id": item["persona_id"],
                "model_label": model_cfg["label"],
                "provider": model_cfg["provider"],
                "model": model_cfg["model"],
                "policy": args.policy,
                "user_prompt": item["user_prompt"],
                "expected_scope": item.get("expected_scope"),
                "expected_drift": item.get("expected_drift"),
                "success": True,
                "original_response": result.content,
                "final_response": final_content,
                "final_stability": final_stability,
                "drift_result": drift_result,
                "repair_result": repair_result,
            })

    save_results(experiment_id, config, records)


if __name__ == "__main__":
    asyncio.run(main())
