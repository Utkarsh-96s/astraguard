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

    # Notification Core & Secrets
    SECRET_KEY: str = "astraguard-dev-secret-key-change-in-production"
    WEB_BASE_URL: str = "http://localhost:3000"
    API_BASE_URL: str = "http://localhost:8000"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = "AstraGuardAlertsBot"
    TELEGRAM_WEBHOOK_SECRET: str = ""
    TELEGRAM_MODE: str = "polling"

    # Web Push (VAPID)
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_ADMIN_EMAIL: str = "mission-safety@astraguard.esa.int"

    # ntfy Push Alerts
    NTFY_BASE_URL: str = "https://ntfy.sh"

    # SMTP Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "alerts@astraguard.esa.int"
    SMTP_USE_TLS: bool = True

    # Twilio SMS (Optional)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # Outbox & Escalation Worker
    OUTBOX_WORKER_INTERVAL_SEC: float = 1.0
    ESCALATION_CHECK_INTERVAL_SEC: float = 2.0


settings = Settings()
