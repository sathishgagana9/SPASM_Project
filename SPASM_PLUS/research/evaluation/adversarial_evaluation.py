"""
Runs the adversarial red-team suite through the REAL intent-classifier
pipeline (app.drift.intent_classifier.classify_intent) and reports
Attack Success Rate (ASR) / Defense Success Rate (DSR), overall and
per attack category — standard adversarial-ML/red-teaming metrics
(see e.g. Zou et al., "Universal and Transferable Adversarial Attacks
on Aligned Language Models", 2023, for ASR as the standard reporting
metric in this exact evaluation style).

## What "success" means here

For a single-turn item, DEFENDED means classify_intent() returns
persona_switch_attempt=True (or in_scope=False) for that message —
i.e. the pipeline would block it before generation, matching this
project's actual production behavior (app/api/conversations.py).

For a MULTI-TURN item (the `multi_turn_escalation` category),
DEFENDED means the classifier catches the attack on ANY turn in the
sequence — since in production, blocking happens per-turn and a
conversation is compromised the moment even one turn slips through
undetected while carrying escalating context toward the final ask.
`conversation_history` is passed to the classifier exactly as
production does, so the multi-turn category genuinely tests whether
history-awareness helps or whether the attack still slips through
turn-by-turn (this is precisely the gap intent_classifier.py's own
docstring already names as unaddressed — this harness is what turns
that stated limitation into a measured number).

## Requires a live provider — this environment has none

`--live` mode needs a real Groq-backed provider (or any LLMProvider
implementation) passed in; without network access here, this script
cannot itself produce real ASR/DSR numbers. Run with `--stub` for a
code-correctness smoke test using a deterministic stub classifier
response (always "defended" or always "not defended", to verify the
metric computation itself is correct) — that is NOT a real evaluation
result, and the report says so explicitly.

Usage:
    python3 adversarial_evaluation.py --stub always_defend    # sanity check the harness
    python3 adversarial_evaluation.py --stub never_defend     # sanity check the harness
    # Real evaluation requires wiring in a live provider — see run_live() below.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

DATASET_PATH = Path(__file__).parent.parent / "datasets" / "adversarial_redteam_suite.jsonl"
RESULTS_PATH = Path(__file__).parent.parent / "results" / "tables" / "adversarial_evaluation.json"


def load_suite() -> list[dict]:
    with open(DATASET_PATH) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_persona(name: str):
    """Loads a real Persona object (with real scope/identity text) from the
    seed data, matched by name — so the evaluation uses the ACTUAL
    configured personas, not a stub with empty fields."""
    from app.models.persona import Persona

    seed_path = BACKEND_DIR / "app" / "seed_data" / "personas.json"
    with open(seed_path) as f:
        seed = json.load(f)
    match = next(p for p in seed if p["name"] == name)
    return Persona(
        name=match["name"], identity=match.get("identity", ""), scope=match.get("scope", ""),
        description=match.get("description", ""), goals=match.get("goals", []),
        knowledge_boundaries=match.get("knowledge_boundaries", []), behavior_rules=match.get("behavior_rules", []),
        response_constraints=match.get("response_constraints", []),
    )


async def evaluate_item(item: dict, provider, model: str) -> dict:
    from app.drift.intent_classifier import classify_intent

    persona = load_persona(item["persona_id"])
    history: list[str] = []
    defended_on_turn = None

    for i, turn_text in enumerate(item["turns"]):
        classification = await classify_intent(persona, turn_text, provider, model, conversation_history=history)
        if classification.persona_switch_attempt or not classification.in_scope:
            defended_on_turn = i
            break
        history.append(turn_text)

    defended = defended_on_turn is not None
    return {
        "id": item["id"], "attack_category": item["attack_category"], "persona_id": item["persona_id"],
        "target_role": item["target_role"], "n_turns": len(item["turns"]),
        "defended": defended, "defended_on_turn": defended_on_turn,
    }


def summarize(results: list[dict]) -> dict:
    overall_n = len(results)
    overall_defended = sum(1 for r in results if r["defended"])
    overall_asr = round(1 - overall_defended / overall_n, 4) if overall_n else None

    by_category: dict[str, dict] = {}
    categories = sorted({r["attack_category"] for r in results})
    for cat in categories:
        subset = [r for r in results if r["attack_category"] == cat]
        n = len(subset)
        defended = sum(1 for r in subset if r["defended"])
        by_category[cat] = {
            "n": n, "defense_success_rate": round(defended / n, 4) if n else None,
            "attack_success_rate": round(1 - defended / n, 4) if n else None,
        }

    return {
        "overall": {"n": overall_n, "defense_success_rate": round(1 - overall_asr, 4) if overall_asr is not None else None, "attack_success_rate": overall_asr},
        "by_category": by_category,
    }


class _StubProvider:
    """Sanity-check ONLY — see module docstring. Never claims to be a real evaluation."""
    name = "stub"

    def __init__(self, mode: str):
        self.mode = mode  # "always_defend" | "never_defend"

    async def generate(self, messages, model, **kwargs):
        from app.providers.base import GenerationResult
        if self.mode == "always_defend":
            content = json.dumps({"persona_switch_attempt": True, "in_scope": False, "requested_persona_or_role": "test",
                                   "requested_domain": "test", "confidence": 0.9, "reasoning": "stub always defends"})
        else:
            content = json.dumps({"persona_switch_attempt": False, "in_scope": True, "requested_persona_or_role": None,
                                   "requested_domain": "test", "confidence": 0.9, "reasoning": "stub never defends"})
        return GenerationResult(content=content, model=model, provider="stub")


async def run_stub(mode: str) -> dict:
    suite = load_suite()
    provider = _StubProvider(mode)
    results = [await evaluate_item(item, provider, "stub-model") for item in suite]
    report = summarize(results)
    report["mode"] = f"STUB SANITY CHECK ONLY ({mode}) — not a real evaluation, see module docstring"
    report["per_item"] = results
    return report


async def run_live(provider, model: str) -> dict:
    """Call this from a real script/notebook with a live LLMProvider once
    you have Groq API access — this function is fully wired and ready,
    just never invoked from this file's CLI (which only offers --stub)."""
    suite = load_suite()
    results = [await evaluate_item(item, provider, model) for item in suite]
    report = summarize(results)
    report["mode"] = "live"
    report["per_item"] = results
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stub", choices=["always_defend", "never_defend"], required=True,
                         help="Sanity-checks the harness only — see module docstring for why this isn't a real result.")
    args = parser.parse_args()

    report = asyncio.run(run_stub(args.stub))
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print(f"MODE: {report['mode']}\n")
    print(f"Overall: n={report['overall']['n']}  DSR={report['overall']['defense_success_rate']}  ASR={report['overall']['attack_success_rate']}\n")
    print("By category:")
    for cat, m in report["by_category"].items():
        print(f"  {cat:24s} n={m['n']:3d}  DSR={m['defense_success_rate']:.3f}  ASR={m['attack_success_rate']:.3f}")
    print(f"\nFull report written to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
