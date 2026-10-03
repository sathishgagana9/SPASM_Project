"""
Provider abstraction — the app must never depend on a specific
LLM backend directly. Every provider implements this interface.
"""
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class GenerationResult:
    content: str
    model: str
    provider: str
    raw: dict | None = None


class ProviderError(Exception):
    """
    Raised for any provider-level failure. `kind` classifies the
    failure so the API layer can return a distinct error_type instead
    of collapsing every failure into one generic message — a timeout
    and an unreachable host need different user-facing copy
    ("Groq took too long" vs "Groq isn't reachable").
    """

    def __init__(self, message: str, kind: str = "unknown"):
        super().__init__(message)
        self.kind = kind  # "timeout" | "unreachable" | "auth" | "rate_limit" | "malformed" | "unknown"


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, messages: list[ChatMessage], model: str, **kwargs) -> GenerationResult:
        ...

    @abstractmethod
    async def stream(self, messages: list[ChatMessage], model: str, **kwargs) -> AsyncIterator[str]:
        """Yields content deltas as they arrive. Implementations should still
        raise ProviderError (not swallow) on failure, ideally before yielding
        anything so the caller can fall back cleanly."""
        ...
        yield ""  # pragma: no cover — makes this an async generator for the type checker

    @abstractmethod
    async def list_models(self) -> list[str]:
        ...

    @abstractmethod
    async def health(self) -> dict:
        ...
