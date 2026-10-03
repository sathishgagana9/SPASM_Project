"""
Fused drift detector — the "detector-as-contribution" upgrade.

## What this replaces

Before this module, the three signal sources in this codebase —
rule-based dimension scores (rules.py), lexical/embedding topical
similarity (semantic.py), and (previously nonexistent) an LLM-judge
score — were never combined. `detector.py` used the rule scores
directly and `scope.py` used similarity only for its own dimension.
There was no principled way to ask "given all three signal sources,
what's the best estimate of drift?" — each backend just did its own
thing independently. That's the "hybrid rule + lexical" pattern the
project's own recommendation review correctly flagged as reading
like a workaround, not a method.

## What this is

A small, dependency-free logistic-regression fusion layer:

    fused_probability = sigmoid(w · x + b)

where x is a feature vector built from ALL available signals (the 8
rule-based dimension scores, scope topical similarity, is_refusal,
and — when available — an LLM-judge score) and w/b are fit by
gradient descent on labeled data (`research/datasets/annotations.jsonl`
once real annotations exist, or any list of (features, label) pairs).

This is a genuine (if simple) learned model, not a fixed weighted
average: the fusion weights are DATA-DRIVEN, and the module reports
whether each dimension's learned weight is positive/negative/near-zero
so the fusion itself becomes an interpretable finding ("the fused
model learned that `scope` and `behavior` carry most of the signal,
`tone` carries almost none" is exactly the kind of statement Part A's
"make the detector itself the contribution" ask is looking for).

## Honesty status (same discipline as the rest of this codebase)

- Until `LogisticFusion.fit()` has been called on real labeled data,
  `predict()` uses the same equal-weight fallback the rest of the
  detector uses today — this module does NOT invent authority it
  hasn't earned. `is_trained` is False and every prediction is
  tagged accordingly in the returned dict.
- The LLM-judge feature slot (`llm_judge_score`) is an interface,
  not an implementation: `app/drift/judge.py` defines the protocol
  and a null backend. Wiring a real LLM call in requires network
  access this environment doesn't have — see judge.py docstring.
- Gradient descent here is plain batch GD with L2 regularization,
  implemented in pure Python for the same dependency-free reason as
  research/evaluation/. For anything beyond the pilot scale, refit
  with sklearn.linear_model.LogisticRegression as a cross-check
  before trusting these weights in a paper, exactly as
  annotator_agreement.py asks you to cross-check kappa/alpha.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

FUSION_VERSION = "raise-fusion-v1.0.0"

# Order matters — this IS the feature vector layout. Keep in sync with
# _feature_vector() and any persisted weights file.
FEATURE_NAMES = [
    "identity", "scope", "behavior", "tone", "goals",
    "knowledge", "instruction", "context",
    "scope_topical_similarity", "is_refusal", "llm_judge_score",
]


def _sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


@dataclass
class FusionExample:
    """One training point. `dimensions` matches detect_drift()'s `dimensions` dict.
    `scope_topical_similarity` and `is_refusal` come from the scope_classification
    extras. `llm_judge_score` is optional (None if not available for this example —
    missing values are mean-imputed at fit time, see fit())."""
    dimensions: dict[str, float]
    scope_topical_similarity: float | None
    is_refusal: bool
    label_drift: bool  # ground truth: True = drift occurred
    llm_judge_score: float | None = None


@dataclass
class LogisticFusion:
    weights: list[float] = field(default_factory=lambda: [0.0] * len(FEATURE_NAMES))
    bias: float = 0.0
    is_trained: bool = False
    n_training_examples: int = 0
    feature_means_for_imputation: list[float] = field(default_factory=lambda: [0.5] * len(FEATURE_NAMES))
    train_accuracy: float | None = None

    # ---- feature extraction ----

    def _feature_vector(self, ex: FusionExample) -> list[float]:
        dims = ex.dimensions
        raw = [
            dims.get("identity", 1.0), dims.get("scope", 1.0), dims.get("behavior", 1.0),
            dims.get("tone", 1.0), dims.get("goals", 1.0), dims.get("knowledge", 1.0),
            dims.get("instruction", 1.0), dims.get("context", 1.0),
            ex.scope_topical_similarity if ex.scope_topical_similarity is not None else float("nan"),
            1.0 if ex.is_refusal else 0.0,
            ex.llm_judge_score if ex.llm_judge_score is not None else float("nan"),
        ]
        # Mean-impute anything missing using whatever this instance last learned
        # (or the neutral defaults below, pre-fit).
        return [
            v if not math.isnan(v) else self.feature_means_for_imputation[i]
            for i, v in enumerate(raw)
        ]

    # ---- training ----

    def fit(self, examples: list[FusionExample], lr: float = 0.1, epochs: int = 500, l2: float = 0.01) -> dict:
        """Batch gradient descent, pure Python. Returns a small training report
        (final loss, train accuracy) rather than mutating silently, so callers
        can sanity-check convergence before trusting the fitted weights."""
        if not examples:
            raise ValueError("fit() requires at least one labeled example")

        # Compute per-feature means over non-missing values, for imputation —
        # done BEFORE training so train-time and predict-time imputation match.
        n_feat = len(FEATURE_NAMES)
        sums = [0.0] * n_feat
        counts = [0] * n_feat
        raw_rows = []
        for ex in examples:
            dims = ex.dimensions
            raw = [
                dims.get("identity", 1.0), dims.get("scope", 1.0), dims.get("behavior", 1.0),
                dims.get("tone", 1.0), dims.get("goals", 1.0), dims.get("knowledge", 1.0),
                dims.get("instruction", 1.0), dims.get("context", 1.0),
                ex.scope_topical_similarity if ex.scope_topical_similarity is not None else float("nan"),
                1.0 if ex.is_refusal else 0.0,
                ex.llm_judge_score if ex.llm_judge_score is not None else float("nan"),
            ]
            raw_rows.append(raw)
            for i, v in enumerate(raw):
                if not math.isnan(v):
                    sums[i] += v
                    counts[i] += 1
        self.feature_means_for_imputation = [
            (sums[i] / counts[i]) if counts[i] else 0.5 for i in range(n_feat)
        ]

        rows = [
            [v if not math.isnan(v) else self.feature_means_for_imputation[i] for i, v in enumerate(raw)]
            for raw in raw_rows
        ]
        labels = [1.0 if ex.label_drift else 0.0 for ex in examples]

        n = len(rows)
        w = [0.0] * n_feat
        b = 0.0
        for _epoch in range(epochs):
            grad_w = [0.0] * n_feat
            grad_b = 0.0
            for row, y in zip(rows, labels):
                z = sum(wi * xi for wi, xi in zip(w, row)) + b
                pred = _sigmoid(z)
                error = pred - y
                for i in range(n_feat):
                    grad_w[i] += error * row[i]
                grad_b += error
            for i in range(n_feat):
                w[i] -= lr * (grad_w[i] / n + l2 * w[i])
            b -= lr * (grad_b / n)

        self.weights = w
        self.bias = b
        self.is_trained = True
        self.n_training_examples = n

        correct = 0
        final_loss = 0.0
        eps = 1e-9
        for row, y in zip(rows, labels):
            z = sum(wi * xi for wi, xi in zip(w, row)) + b
            pred = _sigmoid(z)
            correct += int((pred >= 0.5) == (y >= 0.5))
            final_loss += -(y * math.log(pred + eps) + (1 - y) * math.log(1 - pred + eps))
        self.train_accuracy = round(correct / n, 4)

        return {
            "n_training_examples": n,
            "train_accuracy": self.train_accuracy,
            "final_loss": round(final_loss / n, 4),
            "weights_by_feature": self.feature_importance(),
        }

    # ---- inference ----

    def predict(self, ex: FusionExample) -> dict:
        x = self._feature_vector(ex)
        if not self.is_trained:
            # Fallback: unweighted mean of the rule-based dims only (matches the
            # rest of the codebase's untrained-default behavior) — no invented
            # authority from an untrained model.
            dims = ex.dimensions
            rule_mean = sum(dims.values()) / max(len(dims), 1) if dims else 1.0
            return {
                "fused_drift_probability": round(1.0 - rule_mean, 4),
                "method": "equal_weight_fallback_untrained",
                "is_trained": False,
            }
        z = sum(wi * xi for wi, xi in zip(self.weights, x)) + self.bias
        p_drift = _sigmoid(z)
        return {
            "fused_drift_probability": round(p_drift, 4),
            "method": "logistic_fusion",
            "is_trained": True,
            "n_training_examples": self.n_training_examples,
        }

    def feature_importance(self) -> dict[str, float]:
        return {name: round(w, 4) for name, w in zip(FEATURE_NAMES, self.weights)}

    # ---- persistence ----

    def save(self, path: str | Path) -> None:
        payload = {
            "fusion_version": FUSION_VERSION,
            "weights": self.weights,
            "bias": self.bias,
            "is_trained": self.is_trained,
            "n_training_examples": self.n_training_examples,
            "feature_means_for_imputation": self.feature_means_for_imputation,
            "train_accuracy": self.train_accuracy,
            "feature_names": FEATURE_NAMES,
        }
        Path(path).write_text(json.dumps(payload, indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "LogisticFusion":
        data = json.loads(Path(path).read_text())
        if data.get("feature_names") != FEATURE_NAMES:
            raise ValueError(
                "Saved fusion weights were trained with a different feature layout "
                f"(saved={data.get('feature_names')}, current={FEATURE_NAMES}) — refit, "
                "don't load stale weights against a changed feature set."
            )
        return cls(
            weights=data["weights"],
            bias=data["bias"],
            is_trained=data["is_trained"],
            n_training_examples=data["n_training_examples"],
            feature_means_for_imputation=data["feature_means_for_imputation"],
            train_accuracy=data.get("train_accuracy"),
        )


def example_from_detect_drift_result(result: dict, label_drift: bool, llm_judge_score: float | None = None) -> FusionExample:
    """Convenience constructor: build a FusionExample directly from a
    detect_drift() return dict (see backend/app/drift/detector.py), so
    experiment logs can be turned into training data without hand-mapping
    fields."""
    return FusionExample(
        dimensions=result.get("dimensions", {}),
        scope_topical_similarity=result.get("scope_similarity"),
        is_refusal=bool(result.get("scope_classification") in {"appropriate_refusal", "over_refusal"}),
        label_drift=label_drift,
        llm_judge_score=llm_judge_score,
    )
