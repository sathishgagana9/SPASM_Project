"""
Read-only API for research experiment results (spec section 30:
"Show experiment results only when actual experiment data exists.
Do not display fake charts or fake percentages.").

Reads directly from research/results/raw/*.json — the same files
research/experiments/common.py::save_results() writes. No database
involved; this is a thin filesystem reader.
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException
import json

router = APIRouter(prefix="/api/experiments", tags=["experiments"])

RESULTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "research" / "results" / "raw"


@router.get("")
async def list_experiments():
    """Returns summaries only (no full record dump) — real data if present, empty list otherwise."""
    if not RESULTS_DIR.exists():
        return []
    summaries = []
    for path in sorted(RESULTS_DIR.glob("*.json"), reverse=True):
        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        summaries.append({
            "experiment_id": data.get("experiment_id", path.stem),
            "timestamp": data.get("timestamp"),
            "git_commit": data.get("git_commit"),
            "n_records": data.get("n_records", 0),
            "models": [m.get("label") for m in data.get("config", {}).get("models", [])],
        })
    return summaries


@router.get("/{experiment_id}")
async def get_experiment(experiment_id: str):
    path = RESULTS_DIR / f"{experiment_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No experiment result with this ID. NOT YET EVALUATED.")
    with open(path) as f:
        return json.load(f)
