"""MonitorMBG — FastAPI Application Factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # ── Startup ──
    # TODO: Initialize DB connection pool, load ML models, etc.
    print("🚀 MonitorMBG backend starting up...")
    yield
    # ── Shutdown ──
    # TODO: Close DB connections, release resources
    print("🛑 MonitorMBG backend shutting down...")


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

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "service": "MonitorMBG"}

    return app


app = create_app()
