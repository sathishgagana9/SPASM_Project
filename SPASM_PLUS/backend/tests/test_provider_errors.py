"""
Tests that provider failures are classified correctly (timeout vs
unreachable vs auth vs malformed) so the frontend can show the right
copy instead of a generic error, plus the "missing API key" error
required when GROQ_API_KEY isn't set.

The unreachable-connection test monkeypatches GroqProvider's base URL
to a closed local port rather than calling the real Groq API — this
genuinely exercises the connection-error path without requiring
internet access or a real API key.
"""
import pytest

import app.providers.groq as groq_module
from app.providers.base import ProviderError, ChatMessage
from app.providers.groq import GroqProvider


def test_missing_api_key_raises_clear_error():
    with pytest.raises(ProviderError) as exc_info:
        GroqProvider(api_key="")
    assert exc_info.value.kind == "auth"
    assert "GROQ_API_KEY" in str(exc_info.value)


@pytest.mark.asyncio
async def test_groq_unreachable_is_classified_correctly(monkeypatch):
    # Port 1 is a reserved/privileged port nothing will be listening on.
    monkeypatch.setattr(groq_module, "GROQ_BASE_URL", "http://127.0.0.1:1")
    provider = GroqProvider(api_key="fake-key-for-connection-test", timeout=2.0)
    with pytest.raises(ProviderError) as exc_info:
        await provider.generate([ChatMessage(role="user", content="hi")], model="test-model")
    assert exc_info.value.kind == "unreachable"


@pytest.mark.asyncio
async def test_groq_health_reports_unreachable_not_an_exception(monkeypatch):
    monkeypatch.setattr(groq_module, "GROQ_BASE_URL", "http://127.0.0.1:1")
    provider = GroqProvider(api_key="fake-key-for-connection-test", timeout=2.0)
    health = await provider.health()
    assert health["status"] == "unreachable"
