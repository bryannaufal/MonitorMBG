"""Report service — business logic for official report processing."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.report import Report
from app.schemas.report import ReportCreate


class ReportService:
    """Handles official report CRUD and document processing orchestration."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: ReportCreate) -> Report:
        """Create a new official report."""
        report = Report(**data.model_dump())
        self.session.add(report)
        await self.session.flush()
        return report

    async def get_by_id(self, report_id: int) -> Report | None:
        """Get a report by its ID."""
        result = await self.session.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()

    async def list_reports(
        self, page: int = 1, size: int = 20, region: str | None = None
    ) -> tuple[list[Report], int]:
        """List reports with optional region filter and pagination."""
        query = select(Report)
        if region:
            query = query.where(Report.region == region)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0

        query = query.order_by(Report.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        result = await self.session.execute(query)

        return list(result.scalars().all()), total

    async def update_ocr_result(self, report_id: int, extracted_text: str) -> None:
        """Update a report with OCR-extracted text."""
        report = await self.get_by_id(report_id)
        if report:
            report.ocr_extracted_text = extracted_text
            await self.session.flush()
