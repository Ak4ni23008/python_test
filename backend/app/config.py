"""Application configuration — all secrets from environment (Railway)."""

from __future__ import annotations

import os
from functools import lru_cache

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from repo root (back_testing/) when running from backend/
_ENV_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILES = (
    _ENV_ROOT / ".env",
    Path(".env"),
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(p) for p in _ENV_FILES if p.exists()] or ".env",
        extra="ignore",
    )

    app_name: str = "CloudTrade"
    environment: str = "development"
    database_url: str = "sqlite:///./cloudtrade.db"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    rate_limit_per_minute: int = 60
    worker_poll_seconds: float = 2.0
    cloud_region: str = "railway"
    railway_environment: str = ""
    railway_project_id: str = ""
    dhan_client_id: str = ""
    dhan_access_token: str = ""

    @property
    def is_railway(self) -> bool:
        return bool(self.railway_environment or self.railway_project_id or os.getenv("RAILWAY_ENVIRONMENT"))

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./cloudtrade.db"),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        environment=os.getenv("ENVIRONMENT", "development"),
        cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"),
        rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
        worker_poll_seconds=float(os.getenv("WORKER_POLL_SECONDS", "2.0")),
        railway_environment=os.getenv("RAILWAY_ENVIRONMENT", ""),
        railway_project_id=os.getenv("RAILWAY_PROJECT_ID", ""),
        dhan_client_id=os.getenv("DHAN_CLIENT_ID", ""),
        dhan_access_token=os.getenv("DHAN_ACCESS_TOKEN", ""),
    )
