from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

personas = [

    "Doctor helping patients",

    "Teacher helping students",

    "Lawyer giving legal advice",

    "Bank Manager assisting customers"
]

conversation = """
I understand your fever.
Can you describe your symptoms?
"""

persona_emb = model.encode(personas)

conversation_emb = model.encode(
    [conversation]
)

scores = cosine_similarity(
    conversation_emb,
    persona_emb
)[0]

ranking = sorted(
    zip(personas, scores),
    key=lambda x: x[1],
    reverse=True
)

print("\nTop Persona Matches:\n")

for persona, score in ranking:

    print(
        persona,
        "->",
        round(score, 4)
    )