"""AI Copilot API — bounded demo assistant endpoints."""

import json

from fastapi import APIRouter
from app.schemas.copilot import CopilotQuery, CopilotResponse
from app import demo_data

router = APIRouter()


@router.post("/chat", response_model=CopilotResponse)
async def chat(query: CopilotQuery):
    """
    Send a query to the AI Copilot.

    Uses RAG (Retrieval-Augmented Generation) to retrieve relevant
    case data and synthesize an informed response for operators.
    """
    return demo_data.copilot_answer(query.message, query.conversation_id)


@router.post("/chat/stream")
async def chat_stream(
    query: CopilotQuery,
):
    """
    Stream a copilot response via SSE for real-time token rendering.
    """
    from sse_starlette.sse import EventSourceResponse

    async def generate():
        result = demo_data.copilot_answer(query.message, query.conversation_id)
        for token in result["answer"].split():
            yield json.dumps({"token": token + " ", "done": False})
        yield json.dumps({"sources": result["sources"], "done": True})

    return EventSourceResponse(generate())


@router.post("/ingest")
async def ingest_documents():
    """
    Trigger re-indexing of case documents into the vector store.
    """
    return {
        "message": "Demo data is already indexed in the bounded copilot service.",
        "documents": len(demo_data.EVIDENCE) + len(demo_data.REPORTS) + len(demo_data.COMPLAINTS),
        "ai_notice": demo_data.DEMO_NOTICE,
    }
