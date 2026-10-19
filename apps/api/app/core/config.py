"""Application configuration via pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core settings loaded from environment variables and .env file."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "ASTRA-GUARD"
    VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"]
    )

    # Database configuration
    # Async for FastAPI
    DATABASE_URL: str = "sqlite+aiosqlite:///./astraguard.db"
    # Sync for Alembic
    DATABASE_SYNC_URL: str = "sqlite:///./astraguard.db"

    # Risk Engine Configuration
    RISK_ENGINE_CONFIG: str = "config/risk_engine.yaml"

    # External APIs
    CELESTRAK_BASE_URL: str = "https://celestrak.org"
    SPACE_TRACK_USER: str = ""
    SPACE_TRACK_PASSWORD: str = ""


settings = Settings()
