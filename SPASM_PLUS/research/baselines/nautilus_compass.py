"""
Nautilus Compass-style black-box drift baseline.

Public description (arXiv:2605.09863): embed the latest prompt/response text
against positive and negative behavioral anchors with BGE-M3, aggregate a
weighted top-k cosine signal, and threshold the resulting alignment/deviation.

This file is a clean-room, minimal baseline implementation for head-to-head
experiments on the SPASM++ benchmark. It is NOT the official Nautilus Compass
code and must not be described as an exact reproduction of its production
plugin/API.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


BASELINE_VERSION = "nautilus-compass-style-v1.0.0"


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _weighted_top_k(values: list[float], k: int) -> float:
    if not values:
        return 0.0
    top = sorted(values, reverse=True)[: max(1, min(k, len(values)))]
    weights = list(range(len(top), 0, -1))
    return sum(v * w for v, w in zip(top, weights)) / sum(weights)


@dataclass
class NautilusCompassStyleBaseline:
    model_name: str = "BAAI/bge-m3"
    top_k: int = 5
    threshold: float = 0.0

    def _model(self):
        # The shared semantic loader uses the configured sentence-transformer
        # backend. We instantiate the requested BGE-M3 model directly here so
        # this baseline is not accidentally evaluated with MiniLM.
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install research/requirements-research.txt for the Nautilus-style baseline") from exc
        return SentenceTransformer(self.model_name)

    def score(self, text: str, positive_anchors: list[str], negative_anchors: list[str]) -> dict:
        if not positive_anchors or not negative_anchors:
            raise ValueError("Both positive and negative anchor sets are required")
        model = self._model()
        texts = [text, *positive_anchors, *negative_anchors]
        vectors = model.encode(texts, normalize_embeddings=True)
        query = vectors[0]
        pos = [_cosine(query, v) for v in vectors[1 : 1 + len(positive_anchors)]]
        neg = [_cosine(query, v) for v in vectors[1 + len(positive_anchors) :]]
        alignment = _weighted_top_k(pos, self.top_k)
        deviation = _weighted_top_k(neg, self.top_k)
        # Higher means more aligned with the persona; lower means closer to
        # negative/drift anchors. The threshold is tuned on a dev split.
        drift_margin = alignment - deviation
        return {
            "version": BASELINE_VERSION,
            "method": "positive_negative_anchor_weighted_top_k_cosine",
            "model": self.model_name,
            "alignment": alignment,
            "deviation": deviation,
            "drift_margin": drift_margin,
            "drift": drift_margin < self.threshold,
        }
