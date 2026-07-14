"""Application configuration.

All configuration is sourced from environment variables (Blueprint Vol. 04:
"No secrets in code; use environment configuration"). Values are read once at
import time into a cached ``Settings`` instance.
"""

from functools import lru_cache

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

    # Runtime initialization. When auto_migrate is on, the backend applies Alembic
    # migrations on startup against the database it will serve, so the schema is
    # always present (no "no such table" errors). seed_on_start loads the initial
    # WES organization (idempotent).
    auto_migrate: bool = True
    seed_on_start: bool = True

    # SQLite default keeps local dev and tests zero-dependency; production uses
    # PostgreSQL via WES_DATABASE_URL (see .env.example / docker-compose).
    database_url: str = "sqlite:///./wes_os.db"

    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:4173,http://127.0.0.1:4173"
    )

    # --- Authentication / JWT (Sprint 04) ---
    # WES_JWT_SECRET MUST be overridden in production. The default is for local
    # development only.
    jwt_secret: str = "dev-insecure-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    refresh_token_remember_days: int = 30
    # Default password applied to seeded employees so they can log in locally.
    seed_default_password: str = "WesOs2026!"

    # --- Provider Platform / secret management (Sprint 11) ---
    # WES_SECRET_KEY encrypts provider credentials at rest. MUST be overridden in
    # production. A per-install random key would rotate ciphertext on restart, so a
    # stable default is used for local dev only.
    secret_key: str = "dev-insecure-secret-key-change-in-production"
    # Active environment profile — provider secrets are scoped to a profile so the
    # same install can hold development / staging / production credentials.
    active_environment: str = "development"
    # Default HTTP timeout (seconds) for live provider API calls.
    provider_http_timeout: float = 60.0

    # --- Autonomous Development Engine (Sprint 13) ---
    # Base directory for per-task git sandboxes. Every autonomous implementation
    # runs in a real, isolated git repository UNDER this path — never the WES,
    # WORLD, or Blueprint repositories. Defaults to a temp location.
    dev_workspace_dir: str = "/tmp/wes-dev-workspaces"

    # --- Enterprise DevOps Platform (Sprint 15) ---
    # Base directory for build artifacts and local (real) deployments — never a
    # real production host. Deployments extract the built artifact and verify it.
    devops_workspace_dir: str = "/tmp/wes-devops"
    # Whether the CI/CD pipeline runs REAL `docker build` steps (requires a Docker
    # daemon). Off by default so the test suite stays fast; enabled in runtime.
    devops_docker_builds: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance."""
    return Settings()
