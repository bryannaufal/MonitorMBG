"""Copilot schemas — request/response DTOs for the AI assistant."""

from pydantic import BaseModel


class CopilotQuery(BaseModel):
    """Schema for a copilot query from an operator."""
    message: str
    conversation_id: str | None = None
    context_filters: dict | None = None  # e.g., {"region": "Jakarta", "date_range": "7d"}
    client_cases: list[dict] | None = None  # runtime overlay cases from frontend


class SourceDocument(BaseModel):
    """A source document retrieved by the RAG pipeline."""
    title: str
    content_snippet: str = ""
    source_type: str  # "complaint", "report", "daily_report"
    source_id: int | str
    relevance_score: float


class CopilotResponse(BaseModel):
    """Schema for a copilot response."""
    answer: str
    sources: list[SourceDocument] = []
    confidence: float = 0.0
    conversation_id: str | None = None
