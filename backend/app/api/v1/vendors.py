"""Vendor/SPPG watchlist API."""

from fastapi import APIRouter

from app import demo_data

router = APIRouter()


@router.get("")
@router.get("/")
async def list_vendors():
    """List vendors/SPPG sorted by risk score."""
    items = sorted(demo_data.VENDORS, key=lambda item: item["risk_score"], reverse=True)
    return {"items": items, "total": len(items)}


@router.get("/{vendor_id}")
async def get_vendor(vendor_id: str):
    """Get a vendor/SPPG risk profile."""
    return demo_data.vendor_profile(vendor_id)
