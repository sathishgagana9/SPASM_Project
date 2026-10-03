"""
Turns the RESEARCH.md scope-detection anecdote into a quantified
finding (Part A: "run the lexical-vs-embedding-vs-LLM-judge
comparison across the full benchmark ... report precision/recall/AUROC
for each, and characterize *when* lexical similarity fails, not just
give a hand-picked example").

Runs the SIMILARITY PRIMITIVE directly (app.drift.semantic.similarity)
against `research/datasets/scope_benchmark_expanded.jsonl`
(`generate_scope_benchmark.py`) — i.e. this isolates the
scope-detection question ("does this prompt's topical similarity to
the persona's scope predict whether it's actually in/out of scope?")
from the full detect_drift() pipeline, which is the right unit of
analysis for this specific finding (the RESEARCH.md bug is in the
similarity primitive, not in refusal detection or the other 7
dimensions).

## What runs without network access

- **Lexical backend**: always runs (pure Python, no dependencies).
- **Embedding backend**: runs IF `sentence-transformers` is installed
  and `SPASM_SEMANTIC_BACKEND=embeddings` is set — this needs a one-time
  model download, so it will silently be skipped (reported as
  `"not_run"`) in a no-network environment. This script does NOT fail
  if the embedding backend is unavailable; it reports what it could
  and couldn't run, honestly, same as everywhere else in this codebase.
- **LLM-judge column**: always reported as `"not_run"` here — see
  `backend/app/drift/judge.py`. Wiring this in is a few lines
  (call `GroqJudge.score()` per item) once you have API access; left
  out of this script rather than faked.

Usage: `python3 scope_comparison.py` from this directory.
"""
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(REPO_ROOT))

DATASET_PATH = Path(__file__).parent.parent / "datasets" / "scope_benchmark_expanded.jsonl"
RESULTS_PATH = Path(__file__).parent.parent / "results" / "tables" / "scope_comparison.json"

# Reuse the app's own thresholds so this evaluates the ACTUAL deployed
# classifier's decision boundary, not some other threshold we made up.
OUT_OF_SCOPE_THRESHOLD = 0.06
PERSONA_SCOPES = None  # populated in main() from the app's seed personas


def load_benchmark() -> list[dict]:
    with open(DATASET_PATH) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_persona_scopes() -> dict[str, str]:
    seed_path = BACKEND_DIR / "app" / "seed_data" / "personas.json"
    with open(seed_path) as f:
        personas = json.load(f)
    return {p["name"]: p.get("scope", "") for p in personas}


def evaluate_backend(items: list[dict], scopes: dict[str, str], backend: str) -> dict | None:
    """backend: 'lexical' or 'embeddings'. Returns None if the backend can't run."""
    os.environ["SPASM_SEMANTIC_BACKEND"] = backend
    from app.drift.semantic import similarity  # re-imported per call so the env var takes effect

    scores = []       # continuous: higher = more likely out-of-scope, for AUROC
    predictions = []  # binary at the app's real threshold
    labels = []        # ground truth: True = actually out of scope
    per_item = []
    backend_actually_used = None

    for item in items:
        scope_text = scopes.get(item["persona_id"], "")
        sim, used = similarity(item["user_prompt"], scope_text)
        if backend == "embeddings" and used != "embeddings":
            return None  # embeddings requested but unavailable — bail out cleanly, caller reports "not_run"
        backend_actually_used = used
        drift_score = 1.0 - sim
        predicted_out_of_scope = sim < OUT_OF_SCOPE_THRESHOLD
        label_out_of_scope = item["expected_scope"] == "out_of_scope"

        scores.append(drift_score)
        predictions.append(predicted_out_of_scope)
        labels.append(label_out_of_scope)
        per_item.append({
            "id": item["id"], "category": item["category"], "persona_id": item["persona_id"],
            "similarity": round(sim, 4), "predicted_out_of_scope": predicted_out_of_scope,
            "label_out_of_scope": label_out_of_scope, "correct": predicted_out_of_scope == label_out_of_scope,
        })

    from research.evaluation.metrics import accuracy, precision, recall, f1_score, auroc

    overall = {
        "backend": backend_actually_used,
        "n": len(items),
        "accuracy": round(accuracy(predictions, labels), 4),
        "precision": round(precision(predictions, labels), 4),
        "recall": round(recall(predictions, labels), 4),
        "f1": round(f1_score(predictions, labels), 4),
        "auroc": auroc(scores, labels),
    }

    by_category: dict[str, dict] = {}
    categories = sorted({item["category"] for item in items})
    for cat in categories:
        idx = [i for i, item in enumerate(items) if item["category"] == cat]
        cat_preds = [predictions[i] for i in idx]
        cat_labels = [labels[i] for i in idx]
        cat_scores = [scores[i] for i in idx]
        by_category[cat] = {
            "n": len(idx),
            "accuracy": round(accuracy(cat_preds, cat_labels), 4),
            "precision": round(precision(cat_preds, cat_labels), 4),
            "recall": round(recall(cat_preds, cat_labels), 4),
            "f1": round(f1_score(cat_preds, cat_labels), 4),
            "auroc": auroc(cat_scores, cat_labels),
        }

    return {"overall": overall, "by_category": by_category, "per_item": per_item}


def main():
    items = load_benchmark()
    if not items:
        print(f"No items found at {DATASET_PATH} — run generate_scope_benchmark.py first.")
        return
    scopes = load_persona_scopes()

    report = {
        "dataset": str(DATASET_PATH.name),
        "n_items": len(items),
        "note": "Ground truth here is programmatic/author-labeled (label_source=synthetic_author_generated), "
                "NOT human-annotated — see generate_scope_benchmark.py and RESEARCH.md. This quantifies the "
                "scope-detection failure mode precisely; it does not by itself satisfy the human-annotation "
                "requirement for Q2 submission.",
        "lexical": evaluate_backend(items, scopes, "lexical"),
    }
    embeddings_result = evaluate_backend(items, scopes, "embeddings")
    report["embeddings"] = embeddings_result if embeddings_result is not None else {
        "status": "not_run", "reason": "sentence-transformers not installed / no network to download model"
    }
    report["llm_judge"] = {"status": "not_run", "reason": "no live LLM access in this environment — see backend/app/drift/judge.py"}

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print(f"n_items = {len(items)}\n")
    print("LEXICAL BACKEND (overall):")
    for k, v in report["lexical"]["overall"].items():
        print(f"  {k}: {v}")
    print("\nLEXICAL BACKEND (by category — accuracy is the meaningful metric here since each")
    print("category is single-label by construction; this IS the quantified finding):")
    for cat, m in report["lexical"]["by_category"].items():
        print(f"  {cat:28s} n={m['n']:3d}  accuracy={m['accuracy']:.3f}  (precision={m['precision']:.2f} recall={m['recall']:.2f})")

    if report["embeddings"].get("status") == "not_run":
        print(f"\nEmbeddings backend: not run ({report['embeddings']['reason']})")
    else:
        print("\nEMBEDDINGS BACKEND (by category):")
        for cat, m in report["embeddings"]["by_category"].items():
            print(f"  {cat:28s} n={m['n']:3d}  accuracy={m['accuracy']:.3f}  (precision={m['precision']:.2f} recall={m['recall']:.2f})")

    print(f"\nFull report written to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
