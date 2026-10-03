import json

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------
# Load Baseline
# -----------------------------

with open(
    "baseline.json",
    "r",
    encoding="utf-8"
) as f:

    baseline = json.load(f)

# -----------------------------
# Load Final
# -----------------------------

with open(
    "final.json",
    "r",
    encoding="utf-8"
) as f:

    final = json.load(f)

# -----------------------------
# Convert To Text
# -----------------------------

baseline_text = " ".join(
    baseline.values()
)

final_text = " ".join(
    final.values()
)

# -----------------------------
# Embedding Model
# -----------------------------

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

baseline_emb = model.encode(
    [baseline_text]
)

final_emb = model.encode(
    [final_text]
)

# -----------------------------
# Similarity
# -----------------------------

similarity = cosine_similarity(
    baseline_emb,
    final_emb
)[0][0]

drift_score = 1 - similarity

print(
    f"Similarity: {similarity:.4f}"
)

print(
    f"Probe Drift Score: {drift_score:.4f}"
)