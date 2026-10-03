"""
Application configuration.

Loaded from environment variables (see .env.example). Never hard-code
secrets here — this file only defines defaults and types.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./spasm.db"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # LLM Provider — Groq only. GroqProvider raises a clear ProviderError
    # at construction time if this is empty (see providers/groq.py).
    groq_api_key: str = ""

    # Drift detection thresholds (PROVISIONAL — see docs/drift-detection.md)
    drift_severity_low_threshold: float = 0.85
    drift_severity_medium_threshold: float = 0.70
    drift_severity_high_threshold: float = 0.50


@lru_cache
def get_settings() -> Settings:
    return Settings()
