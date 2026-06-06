"""Aggregated API v1 router — collects all domain routers."""

from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    audit_trail,
    cases,
    copilot,
    complaints,
    daily_reports,
    evidence,
    nutrition,
    reports,
    scoring,
    tickets,
    vendors,
)

api_v1_router = APIRouter()

api_v1_router.include_router(cases.router, prefix="/cases", tags=["Cases"])
api_v1_router.include_router(complaints.router, prefix="/complaints", tags=["Complaints"])
api_v1_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_v1_router.include_router(daily_reports.router, prefix="/daily-reports", tags=["Daily Reports"])
api_v1_router.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])
api_v1_router.include_router(nutrition.router, prefix="/nutrition", tags=["Nutrition"])
api_v1_router.include_router(scoring.router, prefix="/scoring", tags=["Scoring"])
api_v1_router.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
api_v1_router.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])
api_v1_router.include_router(audit_trail.router, prefix="/audit-trail", tags=["Audit Trail"])
api_v1_router.include_router(copilot.router, prefix="/copilot", tags=["AI Copilot"])
api_v1_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
