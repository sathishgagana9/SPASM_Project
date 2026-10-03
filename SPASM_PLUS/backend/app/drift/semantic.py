"""
Semantic similarity layer for the drift detector.

## Honesty note — read this before citing "semantic analysis" anywhere

The default application backend remains bag-of-words cosine similarity so the
product can run without model downloads. The RESEARCH conformal path, however,
requires the explicit neural embedding backend and will fail fast rather than
silently falling back. It captures shared
vocabulary, not meaning: "How do I prepare biryani?" and "What are
the steps for cooking biryani?" score reasonably similar (shared
tokens), but "How do I prepare biryani?" vs a true paraphrase with
no shared words ("What's the process for making that Indian rice
dish with meat and spices?") would score poorly despite meaning the
same thing. This is a real, working, dependency-free proxy — useful
for the common case (in-scope vs. clearly-different-domain
questions, which tend to have near-zero vocabulary overlap), but it
is NOT semantic understanding and should not be described as such in
any paper without this caveat attached.

An OPTIONAL real embedding backend is supported: if
`sentence-transformers` is installed AND `SPASM_SEMANTIC_BACKEND=embeddings`
is set, `get_similarity_fn()` returns a cosine-similarity function
over real sentence embeddings instead. This is not installed by
default (it's a heavy dependency requiring a model download, which
needs network access) — see requirements-research.txt.
"""
import math
import os
import re
from collections import Counter
from functools import lru_cache

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "to", "of", "and", "or",
    "in", "on", "at", "for", "with", "about", "as", "by", "this", "that", "it", "i", "you", "do",
    "does", "did", "can", "could", "would", "should", "will", "shall", "my", "your", "me", "how",
    "what", "please", "help", "explain",
}

_TOKEN_RE = re.compile(r"[a-z0-9']+")


def _tokenize(text: str) -> list[str]:
    tokens = _TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


def _bow_vector(text: str) -> Counter:
    return Counter(_tokenize(text))


def lexical_cosine_similarity(text_a: str, text_b: str) -> float:
    """Bag-of-words cosine similarity, dependency-free. Range [0, 1]. See module docstring."""
    vec_a, vec_b = _bow_vector(text_a), _bow_vector(text_b)
    if not vec_a or not vec_b:
        return 0.0
    shared = set(vec_a) & set(vec_b)
    dot = sum(vec_a[t] * vec_b[t] for t in shared)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


@lru_cache(maxsize=1)
def _try_load_embedding_backend():
    """Attempts to load sentence-transformers. Cached so we only try once per process.
    Returns None if unavailable or not requested — callers must handle that."""
    if os.environ.get("SPASM_SEMANTIC_BACKEND", "lexical") != "embeddings":
        return None
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError:
        return None
    return SentenceTransformer(os.environ.get("SPASM_EMBEDDING_MODEL", "all-MiniLM-L6-v2"))


def embedding_cosine_similarity(text_a: str, text_b: str) -> float | None:
    """Returns None if the embedding backend isn't available/configured — callers
    should fall back to lexical_cosine_similarity in that case."""
    model = _try_load_embedding_backend()
    if model is None:
        return None
    import numpy as np  # only imported if the embedding backend actually loaded

    vecs = model.encode([text_a, text_b])
    a, b = vecs[0], vecs[1]
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def embed_text(text: str) -> list[float] | None:
    """Returns a real sentence-embedding vector for `text`, or None if the
    embedding backend isn't available/configured. Added for
    app.drift.conformal, which needs actual vectors (not just a pairwise
    similarity score) to build a reference-set nonconformity distribution."""
    model = _try_load_embedding_backend()
    if model is None:
        return None
    vec = model.encode([text])[0]
    return [float(x) for x in vec]


def similarity(text_a: str, text_b: str) -> tuple[float, str]:
    """Returns (score, backend_used). Tries embeddings first (only if configured),
    falls back to lexical cosine similarity — this fallback always succeeds."""
    embedded = embedding_cosine_similarity(text_a, text_b)
    if embedded is not None:
        return embedded, "embeddings"
    return lexical_cosine_similarity(text_a, text_b), "lexical"
