"""Application configuration via environment variables."""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global settings loaded from .env file or environment variables."""

    # ── Database ──
    DATABASE_URL: str = "postgresql+asyncpg://monitor_mbg:monitor_mbg_secret@localhost:5432/monitor_mbg"

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Security ──
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── CORS ──
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # ── AI / ML ──
    OPENAI_API_KEY: str = ""
    HUGGINGFACE_TOKEN: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
