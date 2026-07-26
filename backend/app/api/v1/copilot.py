"""AI Copilot API — RAG-backed case summary assistant."""

import json

from fastapi import APIRouter
from app.schemas.copilot import CopilotQuery, CopilotResponse
from app import demo_data
from app.services.copilot.service import reindex_all_cases
from app.services.copilot.synthesizer import synthesizer

router = APIRouter()


@router.post("/chat", response_model=CopilotResponse)
async def chat(query: CopilotQuery):
    """
    Send a query to the AI Copilot.

    Uses in-memory RAG over case documents + Kimi synthesis when configured.
    Falls back to bounded keyword logic if RAG/Kimi unavailable.
    """
    result = await synthesizer.generate(
        query.message,
        query.context_filters,
        query.conversation_id,
        query.client_cases,
    )
    return CopilotResponse(**result)


@router.post("/chat/stream")
async def chat_stream(query: CopilotQuery):
    """Stream a copilot response via SSE for real-time token rendering."""
    from sse_starlette.sse import EventSourceResponse

    async def generate():
        result = await synthesizer.generate(
            query.message,
            query.context_filters,
            query.conversation_id,
            query.client_cases,
        )
        for token in result["answer"].split():
            yield json.dumps({"token": token + " ", "done": False})
        yield json.dumps({"sources": result["sources"], "done": True})

    return EventSourceResponse(generate())


@router.post("/ingest")
async def ingest_documents():
    """Re-index all cases into the in-memory RAG store."""
    stats = reindex_all_cases()
    return {
        "message": f"RAG re-index selesai — {stats['documents']} dokumen.",
        "documents": stats["documents"],
        "embedding_engine": stats["embedding_engine"],
        "ai_notice": demo_data.DEMO_NOTICE,
    }
