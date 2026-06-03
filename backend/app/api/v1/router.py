"""Aggregated API v1 router — collects all domain routers."""

from fastapi import APIRouter

from app.api.v1 import (
    complaints,
    reports,
    daily_reports,
    nutrition,
    scoring,
    copilot,
    analytics,
)

api_v1_router = APIRouter()

api_v1_router.include_router(complaints.router, prefix="/complaints", tags=["Complaints"])
api_v1_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_v1_router.include_router(daily_reports.router, prefix="/daily-reports", tags=["Daily Reports"])
api_v1_router.include_router(nutrition.router, prefix="/nutrition", tags=["Nutrition"])
api_v1_router.include_router(scoring.router, prefix="/scoring", tags=["Scoring"])
api_v1_router.include_router(copilot.router, prefix="/copilot", tags=["AI Copilot"])
api_v1_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
