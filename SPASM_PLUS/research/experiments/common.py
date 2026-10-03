"""
Shared utilities for the experiment scripts. Imports from the
backend app package directly (same pattern as
backend/scripts/seed_personas.py) so experiments exercise the real
persona compiler / drift detector / repair engine — not a
reimplementation that could drift out of sync with the actual app.

Run experiment scripts from research/experiments/ with the backend's
venv active, e.g.:

    cd research/experiments
    source ../../backend/.venv/bin/activate
    python experiment_full_spasm.py
"""
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

CONFIG_PATH = Path(__file__).parent / "config.yaml"
RESULTS_DIR = Path(__file__).parent / ".." / "results" / "raw"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def load_jsonl(relative_path: str) -> list[dict]:
    path = Path(__file__).parent / relative_path
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_personas() -> dict:
    """Returns {persona_name: Persona ORM instance (unsaved, in-memory only)}."""
    from app.models.persona import Persona

    config = load_config()
    personas_path = Path(__file__).parent / config["personas_file"]
    with open(personas_path) as f:
        raw = json.load(f)
    return {p["name"]: Persona(**p) for p in raw}


def new_experiment_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _git_commit_hash() -> str | None:
    """Best-effort — returns None if not in a git repo or git isn't available,
    rather than failing the whole experiment run over a provenance nicety."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent, capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def save_results(experiment_id: str, config: dict, records: list[dict]):
    """
    Writes results with full provenance (spec sections 20, 25, 32):
    experiment_id, config, timestamp, git commit, and every per-record result.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{experiment_id}.json"
    payload = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit_hash(),
        "config": config,
        "n_records": len(records),
        "records": records,
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"Saved {len(records)} records to {out_path}")
    return out_path


async def run_single_trial(provider_name: str, model: str, messages, temperature: float) -> dict:
    """Runs one generation and returns timing/token info alongside the result.
    `messages` is a list of app.providers.base.ChatMessage."""
    from app.providers.base import ProviderError
    from app.providers.registry import get_provider

    provider = get_provider(provider_name)
    start = time.monotonic()
    try:
        result = await provider.generate(messages, model=model, temperature=temperature)
        latency_ms = int((time.monotonic() - start) * 1000)
        return {
            "success": True,
            "content": result.content,
            "latency_ms": latency_ms,
            "tokens_approx": len(result.content.split()),  # word-count proxy, NOT a real tokenizer count
            "error": None,
        }
    except ProviderError as e:
        return {
            "success": False,
            "content": "",
            "latency_ms": int((time.monotonic() - start) * 1000),
            "tokens_approx": 0,
            "error": {"message": str(e), "kind": e.kind},
        }
