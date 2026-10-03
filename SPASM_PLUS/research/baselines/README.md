# Public-method baseline adapters

This folder provides **clean-room research implementations/adapters** for the
2026 persona-drift literature that is directly relevant to SPASM++.

## Nautilus Compass

`nautilus_compass.py` implements the public method description: BGE-M3
embeddings, positive/negative behavioral anchors, weighted top-k cosine
aggregation, and a dev-tuned threshold. It is **not** the official Nautilus
Compass code. For exact reproduction, use the official repository and released
anchors/data.

Reference: Wang, *Nautilus Compass: Black-box Persona Drift Detection for
Production LLM Agents*, arXiv:2605.09863 (2026).

## ContextEcho

`contextecho_protocol.py` implements the public snapshot-then-probe protocol
and single-shot anchor mitigation condition. ContextEcho is a benchmark and
long-session evaluation harness rather than a standalone detector, so treating
it as a conventional detector baseline would be methodologically incorrect.

Reference: Ding et al., *ContextEcho: A Benchmark for Persona Drift in Long
Agentic-Coding Sessions*, arXiv:2605.24279 (2026).

## Required disclosure in the paper

Use wording such as:

> We implement clean-room baselines from the public method descriptions for
> head-to-head evaluation. We do not claim byte-for-byte reproduction of the
> authors' released software or datasets.
