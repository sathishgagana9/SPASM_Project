"""
Factory for resolving a provider instance by name.

Groq is the only supported provider (Ollama was removed entirely).
The registry pattern is kept — rather than calling GroqProvider()
directly everywhere — so the rest of the app doesn't hard-code a
concrete provider class; adding a second provider later means adding
one branch here, not touching call sites.
"""
from app.core.config import get_settings
from app.providers.base import LLMProvider, ProviderError
from app.providers.groq import GroqProvider


def get_provider(name: str) -> LLMProvider:
    settings = get_settings()
    if name == "groq":
        return GroqProvider(api_key=settings.groq_api_key)
    raise ProviderError(
        f"Unknown provider: '{name}'. Only 'groq' is supported — Ollama support was removed from this project.",
        kind="malformed",
    )
