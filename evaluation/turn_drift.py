import json

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------
# Load Baseline Persona State
# -----------------------------

with open(
    "baseline.json",
    "r",
    encoding="utf-8"
) as f:

    baseline = json.load(f)

baseline_text = " ".join(
    baseline.values()
)

# -----------------------------
# Simulated Turn States
# -----------------------------

turn_states = {

    5: """
    I am a Civil Servant.
    I feel calm.
    I am dealing with Tax Issues.
    My goal is to resolve them.
    """,

    10: """
    I work in government.
    I am slightly worried.
    I am dealing with financial issues.
    My goal is to find a solution.
    """,

    15: """
    I am not sure about my role.
    I feel confused.
    I have many problems.
    I want help.
    """,

    20: """
    I don't remember my occupation.
    I feel frustrated.
    I don't know what my goal is.
    """
}

# -----------------------------
# Embedding Model
# -----------------------------

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

baseline_emb = model.encode(
    [baseline_text]
)

print("\nTURN DRIFT ANALYSIS\n")

for turn, text in turn_states.items():

    turn_emb = model.encode(
        [text]
    )

    similarity = cosine_similarity(
        baseline_emb,
        turn_emb
    )[0][0]

    drift = 1 - similarity

    print(
        f"Turn {turn} -> Drift Score: {drift:.4f}"
    )