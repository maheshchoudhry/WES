"""Application configuration.

All configuration is sourced from environment variables (Blueprint Vol. 04:
"No secrets in code; use environment configuration"). Values are read once at
import time into a cached ``Settings`` instance.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, loaded from the environment (prefix ``WES_``)."""

    model_config = SettingsConfigDict(
        env_prefix="WES_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "WES Company Engine"
    env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # SQLite default keeps local dev and tests zero-dependency; production uses
    # PostgreSQL via WES_DATABASE_URL (see .env.example / docker-compose).
    database_url: str = "sqlite:///./wes_os.db"

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance."""
    return Settings()
