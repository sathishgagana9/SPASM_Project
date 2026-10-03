"""Provider listing/health API (Phase 1)."""
from fastapi import APIRouter, HTTPException

from app.providers.base import ProviderError
from app.providers.registry import get_provider

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/{name}/models")
async def list_models(name: str):
    try:
        provider = get_provider(name)
        return {"provider": name, "models": await provider.list_models()}
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.get("/{name}/health")
async def provider_health(name: str):
    try:
        provider = get_provider(name)
        return await provider.health()
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
