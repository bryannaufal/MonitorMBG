"""Complaint service — business logic for social listening data."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.complaint import Complaint
from app.schemas.complaint import ComplaintCreate


class ComplaintService:
    """Handles complaint CRUD, deduplication, and querying."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: ComplaintCreate) -> Complaint:
        """Create a new complaint record."""
        complaint = Complaint(**data.model_dump())
        self.session.add(complaint)
        await self.session.flush()
        return complaint

    async def get_by_id(self, complaint_id: int) -> Complaint | None:
        """Get a complaint by its ID."""
        result = await self.session.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        return result.scalar_one_or_none()

    async def list_complaints(
        self,
        page: int = 1,
        size: int = 20,
        sentiment: str | None = None,
        source: str | None = None,
    ) -> tuple[list[Complaint], int]:
        """List complaints with optional filters and pagination."""
        query = select(Complaint)

        if sentiment:
            query = query.where(Complaint.sentiment == sentiment)
        if source:
            query = query.where(Complaint.source == source)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(Complaint.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        result = await self.session.execute(query)

        return list(result.scalars().all()), total

    async def check_duplicate(self, text: str, source: str) -> bool:
        """Check if a similar complaint already exists (basic dedup)."""
        # TODO: Implement fuzzy matching or embedding-based dedup
        result = await self.session.execute(
            select(Complaint).where(
                Complaint.text == text,
                Complaint.source == source,
            )
        )
        return result.scalar_one_or_none() is not None
