"""
Tests for the semantic similarity layer's default (lexical) backend
and the embedding-backend fallback behavior. Does not require
sentence-transformers to be installed — that's the point.
"""
from app.drift.semantic import lexical_cosine_similarity, similarity


def test_identical_text_has_similarity_one():
    assert lexical_cosine_similarity("linked lists in computer science", "linked lists in computer science") == 1.0


def test_disjoint_vocabulary_has_low_similarity():
    sim = lexical_cosine_similarity("academic education and study guidance", "how do I make biryani rice")
    assert sim < 0.1


def test_shared_vocabulary_scores_higher_than_disjoint():
    related = lexical_cosine_similarity("cooking recipes and food preparation", "how do I make biryani")
    unrelated = lexical_cosine_similarity("academic education and study guidance", "how do I make biryani")
    assert related > unrelated


def test_empty_text_returns_zero_not_error():
    assert lexical_cosine_similarity("", "something") == 0.0
    assert lexical_cosine_similarity("something", "") == 0.0


def test_similarity_falls_back_to_lexical_when_embeddings_not_configured(monkeypatch):
    monkeypatch.delenv("SPASM_SEMANTIC_BACKEND", raising=False)
    score, backend = similarity("linked lists", "data structures")
    assert backend == "lexical"
    assert 0.0 <= score <= 1.0
