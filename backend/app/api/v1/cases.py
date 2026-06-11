"""Case-centered oversight API."""

from fastapi import APIRouter, Query

from app import demo_data

router = APIRouter()


@router.get("")
@router.get("/")
async def list_cases(
    priority: str | None = Query(default=None),
    status: str | None = Query(default=None),
    region: str | None = Query(default=None),
    issue: str | None = Query(default=None),
    search: str | None = Query(default=None),
):
    """List case work queue with optional operator filters."""
    items = demo_data.oversight_cases()

    if priority:
        items = [item for item in items if item["priority_label"].lower() == priority.lower()]
    if status:
        items = [item for item in items if status.lower() in item["status"].lower()]
    if region:
        items = [item for item in items if region.lower() in item["region"].lower()]
    if issue:
        items = [item for item in items if issue.lower() in item["issue_category"].lower()]
    if search:
        query = search.lower()
        items = [
            item
            for item in items
            if query in item["title"].lower()
            or query in item["vendor_name"].lower()
            or query in item["school"].lower()
            or query in item["case_id"].lower()
        ]

    return {"items": items, "total": len(items)}


@router.get("/{case_id}")
async def get_case(case_id: str):
    """Get the full investigation hub for one oversight case."""
    return demo_data.case_detail(case_id)
