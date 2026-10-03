"""
Health and provider-status endpoints.

This is the endpoint the frontend polls to show connection status —
there is no fabricated "connected" state; it reflects a real check.
Groq is the only provider (Ollama was removed entirely).
"""
from fastapi import APIRouter

from app.core.config import get_settings
from app.providers.groq import GroqProvider
from app.providers.base import ProviderError

router = APIRouter(prefix="/api/health", tags=["health"])
settings = get_settings()


@router.get("")
async def health():
    return {"status": "ok", "environment": settings.environment}


@router.get("/providers")
async def provider_health():
    """
    Real connectivity check against Groq. Returns 'unreachable' or
    'not configured' rather than fabricating a healthy status.
    """
    if not settings.groq_api_key:
        return {"groq": {"status": "not configured", "detail": "GROQ_API_KEY is not set in backend/.env"}}

    try:
        provider = GroqProvider(api_key=settings.groq_api_key)
        result = await provider.health()
        return {"groq": result}
    except ProviderError as e:
        return {"groq": {"status": "error", "detail": str(e)}}
