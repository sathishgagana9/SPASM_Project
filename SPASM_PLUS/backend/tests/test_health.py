"""
Phase 0 tests: prove the app boots and the DB-backed persona slice
works end to end. Run with: pytest
"""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_persona_create_and_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/personas", json={"name": "Study Mentor", "description": "Formal academic tutor"}
        )
        assert create_resp.status_code == 201
        persona = create_resp.json()
        assert persona["name"] == "Study Mentor"

        list_resp = await client.get("/api/personas")
        assert list_resp.status_code == 200
        names = [p["name"] for p in list_resp.json()]
        assert "Study Mentor" in names
