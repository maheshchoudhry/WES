"""Application configuration loaded from the environment."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "WES API"
    api_version: str = "v1"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://wes:wes@localhost:5432/wes"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
