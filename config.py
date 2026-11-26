"""Centralised, validated configuration loaded from environment variables."""
from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    deepseek_api_key: str = Field(..., alias="DEEPSEEK_API_KEY")
    database_url: str = Field("", alias="DATABASE_URL")
    deepseek_base_url: str = Field("https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field("deepseek-chat", alias="DEEPSEEK_MODEL")
    deepseek_timeout: int = Field(45, alias="DEEPSEEK_TIMEOUT")
    deploy_mode: str = Field("polling", alias="DEPLOY_MODE")
    webhook_url: str = Field("", alias="WEBHOOK_URL")
    webhook_port: int = Field(8080, alias="WEBHOOK_PORT")
    serpapi_key: str = Field("", alias="SERPAPI_KEY")
    trend_provider: str = Field("none", alias="TREND_PROVIDER")

    @field_validator("deploy_mode")
    @classmethod
    def _check_mode(cls, v: str) -> str:
        v = v.lower()
        if v not in {"polling", "webhook"}:
            raise ValueError("DEPLOY_MODE must be 'polling' or 'webhook'")
        return v

    @property
    def sqlalchemy_url(self) -> str:
        url = self.database_url.strip()
        if not url:
            return "sqlite+aiosqlite:///./findora.db"
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
