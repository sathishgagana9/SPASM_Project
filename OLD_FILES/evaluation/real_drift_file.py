import os

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------
# Load Model
# -----------------------------

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

# -----------------------------
# Find Latest Conversation File
# -----------------------------

output_folder = "../output"

files = [

    f for f in os.listdir(output_folder)

    if f.endswith(".txt")
]

latest_file = max(

    files,

    key=lambda x:
    os.path.getctime(
        os.path.join(
            output_folder,
            x
        )
    )
)

file_path = os.path.join(
    output_folder,
    latest_file
)

print(
    f"Evaluating: {latest_file}"
)

# -----------------------------
# Read Conversation
# -----------------------------

with open(
    file_path,
    "r",
    encoding="utf-8"
) as f:

    conversation = f.read()

# -----------------------------
# Persona Reference
# -----------------------------

persona = """
professional
helpful
empathetic
supportive
role-consistent
"""

# -----------------------------
# Embeddings
# -----------------------------

emb1 = model.encode(
    [persona]
)

emb2 = model.encode(
    [conversation]
)

score = cosine_similarity(
    emb1,
    emb2
)

drift = (
    1 - score[0][0]
)

print(
    "Drift Score:",
    round(drift, 4)
)