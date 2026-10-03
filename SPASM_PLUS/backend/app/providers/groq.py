"""
Groq provider — the only LLM provider in this project (Ollama was
removed entirely, per project decision).

Uses Groq's OpenAI-compatible /chat/completions endpoint at
https://api.groq.com/openai/v1. Reads GROQ_API_KEY from settings
(backed by the GROQ_API_KEY env var — see app/core/config.py).
Raises a clear ProviderError immediately if the key is missing,
rather than failing confusingly on the first request.
"""
import json
from collections.abc import AsyncIterator

import httpx

from app.providers.base import ChatMessage, GenerationResult, LLMProvider, ProviderError

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: str, timeout: float = 60.0):
        if not api_key:
            raise ProviderError(
                "GROQ_API_KEY is not set. Add it to backend/.env — get a free key at "
                "https://console.groq.com (API Keys).",
                kind="auth",
            )
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict:
        return {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

    def _client(self, timeout: float | None = None) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=timeout or self.timeout, trust_env=False)

    async def generate(self, messages: list[ChatMessage], model: str, **kwargs) -> GenerationResult:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.7),
        }
        try:
            async with self._client() as client:
                resp = await client.post(f"{GROQ_BASE_URL}/chat/completions", json=payload, headers=self._headers())
        except httpx.TimeoutException as e:
            raise ProviderError("Groq timed out waiting for a response.", kind="timeout") from e
        except httpx.RequestError as e:
            raise ProviderError(f"Could not reach Groq: {e}", kind="unreachable") from e

        if resp.status_code == 401:
            raise ProviderError("Groq rejected the API key (401). Check GROQ_API_KEY in backend/.env.", kind="auth")
        if resp.status_code == 429:
            raise ProviderError("Groq rate limit hit (429). Wait a moment and try again.", kind="rate_limit")
        if resp.status_code == 404:
            raise ProviderError(
                f"Model '{model}' not found on Groq. Check https://console.groq.com/docs/models for a "
                f"currently-available model name — Groq deprecates models periodically.",
                kind="malformed",
            )
        if resp.status_code != 200:
            raise ProviderError(f"Groq returned {resp.status_code}: {resp.text[:300]}", kind="unknown")

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ProviderError("Groq returned a malformed response", kind="malformed") from e
        return GenerationResult(content=content, model=model, provider=self.name, raw=data)

    async def stream(self, messages: list[ChatMessage], model: str, **kwargs) -> AsyncIterator[str]:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "stream": True,
        }
        try:
            async with self._client() as client:
                async with client.stream(
                    "POST", f"{GROQ_BASE_URL}/chat/completions", json=payload, headers=self._headers()
                ) as resp:
                    if resp.status_code == 401:
                        raise ProviderError("Groq rejected the API key (401). Check GROQ_API_KEY in backend/.env.", kind="auth")
                    if resp.status_code == 429:
                        raise ProviderError("Groq rate limit hit (429). Wait a moment and try again.", kind="rate_limit")
                    if resp.status_code == 404:
                        raise ProviderError(
                            f"Model '{model}' not found on Groq. Check https://console.groq.com/docs/models "
                            f"for a currently-available model name.",
                            kind="malformed",
                        )
                    if resp.status_code != 200:
                        body = await resp.aread()
                        raise ProviderError(f"Groq returned {resp.status_code}: {body[:300]}", kind="unknown")

                    async for line in resp.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data_str = line[len("data:"):].strip()
                        if data_str == "[DONE]":
                            break
                        if not data_str:
                            continue
                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue
                        delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if delta:
                            yield delta
        except httpx.TimeoutException as e:
            raise ProviderError("Groq timed out streaming a response.", kind="timeout") from e
        except httpx.RequestError as e:
            raise ProviderError(f"Could not reach Groq: {e}", kind="unreachable") from e

    async def list_models(self) -> list[str]:
        try:
            async with self._client(timeout=5.0) as client:
                resp = await client.get(f"{GROQ_BASE_URL}/models", headers=self._headers())
            resp.raise_for_status()
            return [m["id"] for m in resp.json().get("data", [])]
        except httpx.HTTPError as e:
            raise ProviderError(f"Could not list Groq models: {e}", kind="unreachable") from e

    async def health(self) -> dict:
        try:
            async with self._client(timeout=3.0) as client:
                resp = await client.get(f"{GROQ_BASE_URL}/models", headers=self._headers())
            return {"status": "connected" if resp.status_code == 200 else "error", "base_url": GROQ_BASE_URL}
        except httpx.RequestError:
            return {"status": "unreachable", "base_url": GROQ_BASE_URL}
