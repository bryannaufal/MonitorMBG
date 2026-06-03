"""AI Copilot API — RAG-based assistant endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.copilot import CopilotQuery, CopilotResponse

router = APIRouter()


@router.post("/chat", response_model=CopilotResponse)
async def chat(
    query: CopilotQuery,
    session: AsyncSession = Depends(get_session),
):
    """
    Send a query to the AI Copilot.

    Uses RAG (Retrieval-Augmented Generation) to retrieve relevant
    case data and synthesize an informed response for operators.
    """
    # TODO: Implement via copilot service (retriever + synthesizer)
    return {
        "answer": "Copilot response placeholder",
        "sources": [],
        "confidence": 0.0,
    }


@router.post("/chat/stream")
async def chat_stream(
    query: CopilotQuery,
):
    """
    Stream a copilot response via SSE for real-time token rendering.
    """
    from sse_starlette.sse import EventSourceResponse

    async def generate():
        # TODO: Implement streaming via copilot synthesizer
        yield '{"token": "Streaming ", "done": false}'
        yield '{"token": "response ", "done": false}'
        yield '{"token": "placeholder.", "done": true}'

    return EventSourceResponse(generate())


@router.post("/ingest")
async def ingest_documents(
    session: AsyncSession = Depends(get_session),
):
    """
    Trigger re-indexing of case documents into the vector store.
    """
    # TODO: Dispatch vector store indexing task
    return {"message": "Document ingestion dispatched"}
