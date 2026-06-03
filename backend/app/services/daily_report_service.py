"""Daily Report service — orchestrates photo verification and nutrition pipelines."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.daily_report import DailyReport
from app.schemas.daily_report import DailyReportCreate


class DailyReportService:
    """
    Handles daily report CRUD and orchestrates the multimodal verification pipeline:
    1. Perceptual hash computation → duplicate detection
    2. Image-text similarity matching → verification
    3. Food detection + nutrition estimation
    4. Score computation
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: DailyReportCreate) -> DailyReport:
        """Create a new daily report."""
        report = DailyReport(**data.model_dump())
        self.session.add(report)
        await self.session.flush()
        return report

    async def get_by_id(self, report_id: int) -> DailyReport | None:
        """Get a daily report by its ID."""
        result = await self.session.execute(
            select(DailyReport).where(DailyReport.id == report_id)
        )
        return result.scalar_one_or_none()

    async def list_reports(
        self,
        page: int = 1,
        size: int = 20,
        verification_status: str | None = None,
        region: str | None = None,
    ) -> tuple[list[DailyReport], int]:
        """List daily reports with optional filters."""
        query = select(DailyReport)
        if verification_status:
            query = query.where(DailyReport.verification_status == verification_status)
        if region:
            query = query.where(DailyReport.region == region)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0

        query = query.order_by(DailyReport.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        result = await self.session.execute(query)

        return list(result.scalars().all()), total

    async def update_verification_status(
        self, report_id: int, status: str, verifications: dict | None = None
    ) -> None:
        """Update verification status after CV pipeline completes."""
        report = await self.get_by_id(report_id)
        if report:
            report.verification_status = status
            if verifications:
                report.photo_verifications = verifications
            await self.session.flush()

    async def add_photo_urls(self, report_id: int, urls: list[str]) -> None:
        """Add uploaded photo URLs to a daily report."""
        report = await self.get_by_id(report_id)
        if report:
            existing = report.photo_urls or []
            report.photo_urls = existing + urls
            await self.session.flush()
