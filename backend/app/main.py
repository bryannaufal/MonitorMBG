"""MonitorMBG — FastAPI Application Factory."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(name)s - %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import demo_data, persistence
from app.config import settings
from app.api.v1.router import api_v1_router
from app.services.intake.uploads import UPLOAD_DIR, ensure_upload_dir
from app.services.copilot.service import bootstrap_rag

# Folder dataset asli tidak dipindahkan; hanya disajikan read-only.
_EVIDENCE_DIR = Path(__file__).resolve().parents[2] / "Dataset Gambar"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # ── Startup ──
    # Load persisted state over the seed literals so operator changes from a
    # previous run survive.  Falls back to in-memory demo data if the DB is
    # unavailable or has never been seeded.
    if persistence.hydrate():
        demo_data.rebuild_derived()
        print(f"🗄️  Persistensi aktif — {len(demo_data.oversight_cases())} kasus dimuat dari database.")
    else:
        print("💾 Persistensi nonaktif — memakai data demo in-memory. "
              "Jalankan `python -m app.dbctl seed` untuk mengaktifkan.")
    # Phase-2 intake/RAG bootstrap runs after hydration so the index sees
    # persisted rows, not just the seed literals.
    ensure_upload_dir()
    bootstrap_rag()
    print("🚀 MonitorMBG backend starting up...")
    yield
    # ── Shutdown ──
    # TODO: Close DB connections, release resources
    print("MonitorMBG backend shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="MonitorMBG API",
        description="Makan Bergizi Gratis — Oversight Intelligence and Orchestration Layer",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──
    app.include_router(api_v1_router, prefix="/api/v1")

    # ── Bukti foto (read-only, folder dataset tidak dipindahkan) ──
    if _EVIDENCE_DIR.is_dir():
        app.mount("/evidence-media", StaticFiles(directory=str(_EVIDENCE_DIR)), name="evidence-media")

    if UPLOAD_DIR.is_dir():
        app.mount("/intake-media", StaticFiles(directory=str(UPLOAD_DIR)), name="intake-media")

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "service": "MonitorMBG"}

    return app


app = create_app()
