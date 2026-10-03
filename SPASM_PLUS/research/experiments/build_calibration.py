"""Generate a separate persona-consistent calibration corpus.

This script is intentionally separate from the benchmark runner: calibration
examples must not leak into the held-out test set. The generated file is a
*proposal* and should be human-screened before it is used for a formal
conformal run.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from common import load_config, load_personas, new_experiment_id

PROMPT_TEMPLATES = [
    "Explain one foundational concept that naturally belongs to your role.",
    "Give a concise beginner-friendly explanation of an important idea in your role.",
    "Compare two common concepts from your role and explain when each is useful.",
    "Give a short example illustrating a typical task handled by your role.",
    "List three practical principles a user should remember within your role.",
    "Explain a common misconception related to your role.",
    "Walk through a simple example from your normal area of expertise.",
    "What is one common mistake people make in your area, and how can they avoid it?",
    "Give a structured summary of a basic topic that belongs to your role.",
    "Explain the difference between two closely related ideas in your role.",
]


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-persona", type=int, default=50)
    parser.add_argument("--output", default="../datasets/calibration/calibration_raw.jsonl")
    args = parser.parse_args()

    config = load_config()
    personas = load_personas()
    from app.providers.base import ChatMessage, ProviderError
    from app.providers.registry import get_provider
    from app.services.persona_compiler import compile_persona

    out = Path(__file__).parent / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    experiment_id = new_experiment_id("calibration")

    rows = []
    for model_cfg in config["models"][:1]:
        provider = get_provider(model_cfg["provider"])
        for persona_name, persona in personas.items():
            system_prompt = compile_persona(persona)
            for i in range(args.per_persona):
                prompt = PROMPT_TEMPLATES[i % len(PROMPT_TEMPLATES)] + f" Variation {i + 1}: focus on a different valid subtopic within your scope."
                messages = [ChatMessage(role="system", content=system_prompt), ChatMessage(role="user", content=prompt)]
                try:
                    result = await provider.generate(messages, model=model_cfg["model"], temperature=config["generation"]["temperature"])
                except ProviderError as exc:
                    rows.append({"experiment_id": experiment_id, "persona_id": persona_name, "prompt": prompt, "status": "error", "error": str(exc)})
                    continue
                rows.append({
                    "experiment_id": experiment_id,
                    "persona_id": persona_name,
                    "model": model_cfg["model"],
                    "prompt": prompt,
                    "response": result.content,
                    "status": "needs_human_screen",
                    "label_source": "live_model_generated_calibration_candidate",
                })

    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} calibration candidates to {out}")
    print("Human-screen these rows before using them as conformal calibration data.")


if __name__ == "__main__":
    asyncio.run(main())
