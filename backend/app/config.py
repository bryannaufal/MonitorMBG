"""Application configuration via environment variables."""

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env di root repo (docker-compose) atau backend/.env (override lokal).
_ENV_BACKEND = Path(__file__).resolve().parents[1] / ".env"
_ENV_ROOT = Path(__file__).resolve().parents[2] / ".env"
_ENV_FILES = tuple(str(p) for p in (_ENV_BACKEND, _ENV_ROOT) if p.is_file())


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
    KIMI_API_KEY: str = ""
    KIMI_BASE_URL: str = "https://api.kimi.com/coding/v1"
    KIMI_MODEL: str = "kimi-k2-turbo-preview"
    KIMI_VISION_MODEL: str = ""  # kosong = pakai KIMI_MODEL; live vision gizi dari foto
    KIMI_TIMEOUT_SECONDS: float = 60.0

    # Copilot RAG — Gemini embeddings (Google AI)
    GEMINI_API_KEY: str = ""
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_EMBEDDING_DIM: int = 768
    GEMINI_API_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    GEMINI_TIMEOUT_SECONDS: float = 60.0
    COPILOT_TOP_K: int = 5

    # ── Intake scraper ──
    # fixture = JSON demo lokal | live = fetch eksternal (twitter atau rss)
    SCRAPER_MODE: str = "fixture"
    SCRAPER_LIVE_PROVIDER: str = "twitter"  # twitter | rss | twitter,rss | both
    # Saat scrape: scoring Kimi + gate threshold auto-ticket (Kasus/Tiket otomatis jika lolos)
    AUTO_TICKET_ON_INTAKE: bool = True
    # Post-filter keyword (rss; opsional untuk twitter bila query sudah spesifik)
    SCRAPER_KEYWORDS: str = "mbg,makan bergizi,belatung,keracunan,gizi"

    # twitterapi.io — https://twitterapi.io (header X-API-Key)
    TWITTERAPI_IO_API_KEY: str = ""
    TWITTERAPI_IO_BASE_URL: str = "https://api.twitterapi.io"
    TWITTERAPI_IO_SEARCH_QUERY: str = '(MBG OR "makan bergizi") lang:id -filter:replies'
    TWITTERAPI_IO_QUERY_TYPE: str = "Latest"  # Latest | Top
    SCRAPER_TWITTER_MAX_RESULTS: int = 10

    # Fallback live provider: Google News RSS
    SCRAPER_RSS_URL: str = (
        "https://news.google.com/rss/search?q=MBG+makan+bergizi+indonesia&hl=id&gl=ID&ceid=ID:id"
    )

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES or ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
