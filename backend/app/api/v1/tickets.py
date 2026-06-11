"""Ticket orchestration API — demo case queue and status updates."""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app import demo_data

router = APIRouter()


class TicketStatusUpdate(BaseModel):
    status: str
    actor: str = "Demo Operator"
    note: str | None = None


@router.get("")
@router.get("/")
async def list_tickets():
    """List ticket/case queue sorted by priority."""
    items = sorted(demo_data.TICKETS, key=lambda item: item["priority"], reverse=True)
    return {"items": items, "total": len(items)}


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get a single ticket."""
    return demo_data.get_or_404(demo_data.TICKETS, ticket_id, "Ticket")


@router.patch("/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, update: TicketStatusUpdate):
    """Update ticket status in memory and append a demo audit event."""
    ticket = demo_data.get_or_404(demo_data.TICKETS, ticket_id, "Ticket")
    ticket["status"] = update.status
    ticket["updated_at"] = datetime.now(timezone.utc).isoformat()
    event = {
        "id": len(demo_data.AUDIT_TRAIL) + 1,
        "case_id": ticket["case_id"],
        "ticket_id": ticket["id"],
        "event_type": "status_changed",
        "actor": update.actor,
        "role": "District Operator",
        "description": update.note or f"Ticket status changed to {update.status}.",
        "timestamp": ticket["updated_at"],
    }
    demo_data.AUDIT_TRAIL.insert(0, event)
    return {"ticket": ticket, "audit_event": event, "ai_notice": demo_data.DEMO_NOTICE}
