"""
Tests for chat-history management: auto-title generation, rename,
and delete (with cascade cleanup of drift/repair events). Uses the
ASGI test client against an in-memory-per-test SQLite DB — no live
Ollama needed for these, since they don't hit send_message's
generate() call.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.conversations import _auto_title
from app.main import app


def test_auto_title_short_message():
    assert _auto_title("Explain linked lists") == "Explain linked lists"


def test_auto_title_truncates_long_message():
    long_msg = "Can you give me a very detailed and thorough explanation of how linked lists work internally"
    title = _auto_title(long_msg)
    assert len(title) <= 50
    assert title.endswith("…")


def test_auto_title_capitalizes():
    assert _auto_title("how to make biryani").startswith("How")


@pytest.mark.asyncio
async def test_rename_and_delete_conversation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        persona_resp = await client.post("/api/personas", json={"name": "Test Persona", "scope": "testing"})
        persona_id = persona_resp.json()["id"]

        convo_resp = await client.post(
            "/api/conversations", json={"persona_id": persona_id, "provider": "groq", "model": "test-model"}
        )
        assert convo_resp.status_code == 201
        convo_id = convo_resp.json()["id"]

        rename_resp = await client.patch(f"/api/conversations/{convo_id}", json={"title": "Renamed Chat"})
        assert rename_resp.status_code == 200
        assert rename_resp.json()["title"] == "Renamed Chat"

        delete_resp = await client.delete(f"/api/conversations/{convo_id}")
        assert delete_resp.status_code == 204

        get_messages_resp = await client.get(f"/api/conversations/{convo_id}/messages")
        assert get_messages_resp.status_code == 200
        assert get_messages_resp.json() == []  # conversation gone, no orphaned messages returned


@pytest.mark.asyncio
async def test_missing_groq_key_returns_structured_error_not_a_crash(monkeypatch):
    """
    Regression test for a real bug: get_provider() can raise ProviderError
    (e.g. GROQ_API_KEY missing) but that call wasn't wrapped in try/except
    in send_message or send_message_stream — it crashed as an unhandled
    500 instead of the clean, structured error the frontend expects.
    Forces the exact missing-key scenario via monkeypatch, regardless of
    whatever GROQ_API_KEY happens to be set in the environment running
    this test.
    """
    from app.core.config import Settings

    # registry.py does `from app.core.config import get_settings`, binding its own
    # reference at import time — patch that reference directly.
    import app.providers.registry as registry_module
    monkeypatch.setattr(registry_module, "get_settings", lambda: Settings(groq_api_key=""))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        persona_resp = await client.post("/api/personas", json={"name": "Test Persona", "scope": "testing"})
        persona_id = persona_resp.json()["id"]

        convo_resp = await client.post(
            "/api/conversations", json={"persona_id": persona_id, "provider": "groq", "model": "test-model"}
        )
        convo_id = convo_resp.json()["id"]

        send_resp = await client.post(f"/api/conversations/{convo_id}/messages", json={"content": "hi"})

        # The bug: this used to be a 500 with no usable detail. The fix: a
        # structured 502 with error_type="auth" the frontend can map to
        # clear copy ("check GROQ_API_KEY").
        assert send_resp.status_code != 500, (
            "Missing API key crashed as an unhandled 500 instead of a structured error — "
            "this is the exact bug from the screenshot."
        )
        assert send_resp.status_code == 502
        detail = send_resp.json()["detail"]
        assert detail["error_type"] == "auth"
        assert "GROQ_API_KEY" in detail["message"]


@pytest.mark.asyncio
async def test_repair_events_endpoint_returns_empty_list_for_new_conversation():
    """Smoke test for the new GET /repair-events endpoint, added for the
    turn-by-turn analysis pane (repair events previously had no listing
    endpoint at all — only ever seen live)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        persona_resp = await client.post("/api/personas", json={"name": "Test Persona", "scope": "testing"})
        persona_id = persona_resp.json()["id"]
        convo_resp = await client.post(
            "/api/conversations", json={"persona_id": persona_id, "provider": "groq", "model": "test-model"}
        )
        convo_id = convo_resp.json()["id"]

        resp = await client.get(f"/api/conversations/{convo_id}/repair-events")
        assert resp.status_code == 200
        assert resp.json() == []
