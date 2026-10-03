"""
ContextEcho-style long-session probe/mitigation baseline.

ContextEcho (arXiv:2605.24279) is primarily a benchmark/protocol rather than
a standalone detector. Its public description uses snapshot/fork probes over
long agentic sessions and evaluates a single-shot persona anchor mitigation.
This module implements that *experimental protocol* so SPASM++ can be compared
against the same long-session structure.

It does not claim to reproduce the donated sessions or the full official
ContextEcho harness. Those artifacts remain the authoritative reproduction
source.
"""
from __future__ import annotations

from dataclasses import dataclass

BASELINE_VERSION = "contextecho-style-protocol-v1.0.0"


@dataclass(frozen=True)
class Probe:
    turn_index: int
    prompt: str


def build_snapshot_probe_sequence(session_messages: list[dict], probe_prompts: list[str], turn_indices: list[int]) -> list[dict]:
    """Create reproducible snapshot/fork records without mutating the source session."""
    records = []
    for turn_index in turn_indices:
        prefix = session_messages[: max(0, turn_index)]
        for probe in probe_prompts:
            records.append({
                "version": BASELINE_VERSION,
                "turn_index": turn_index,
                "probe": probe,
                "snapshot_messages": prefix,
                "protocol": "snapshot_then_probe",
            })
    return records


def single_shot_anchor(system_anchor: str, probe: str) -> list[dict]:
    """Construct the fixed-anchor mitigation condition used as a baseline."""
    return [
        {"role": "system", "content": system_anchor},
        {"role": "user", "content": probe},
    ]
