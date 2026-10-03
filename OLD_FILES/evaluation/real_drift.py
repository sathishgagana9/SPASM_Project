from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

persona = """
doctor
professional
polite
helpful
patient care
"""

response = """
Hello. I understand you're worried about your fever, and it's perfectly natural to feel that way when you're not feeling well.

Please don't worry; we're going to look into this together.

To help me understand what might be going on, could you tell me a bit more about it?
"""

emb1 = model.encode([persona])

emb2 = model.encode([response])

score = cosine_similarity(
    emb1,
    emb2
)

print(
    "Similarity:",
    score[0][0]
)

print(
    "Drift Score:",
    1 - score[0][0]
)