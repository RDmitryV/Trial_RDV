"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "Искусанный Интеллектом Маркетолух"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    # API
    api_v1_prefix: str = "/api/v1"

    # Security
    secret_key: str = Field(..., validation_alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=15, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS")
    algorithm: str = "HS256"

    # Database
    database_url: PostgresDsn = Field(..., validation_alias="DATABASE_URL")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", validation_alias="REDIS_URL")

    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/0", validation_alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", validation_alias="CELERY_RESULT_BACKEND")

    # LLM APIs
    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    default_llm_provider: str = Field(default="openai", validation_alias="DEFAULT_LLM_PROVIDER")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        validation_alias="CORS_ORIGINS"
    )

    # Sentry
    sentry_dsn: Optional[str] = Field(default=None, validation_alias="SENTRY_DSN")

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100


settings = Settings()
