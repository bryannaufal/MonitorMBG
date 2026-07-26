"""Copilot orchestration — index cases & answer queries."""

from __future__ import annotations

import logging

from app.services.copilot.rag_store import rag_store

logger = logging.getLogger(__name__)


def bootstrap_rag() -> None:
    rag_store.bootstrap()


def index_case_for_copilot(case_id: str) -> None:
    """Index or refresh one case in the in-memory RAG index."""
    try:
        rag_store.index_case(case_id)
    except Exception as exc:
        logger.warning("Copilot RAG index failed for %s: %s", case_id, exc)


def reindex_all_cases() -> dict:
    rag_store.clear()
    rag_store.bootstrap()
    return {
        "documents": len(rag_store),
        "embedding_engine": rag_store.embedding_engine,
    }


def prepare_copilot_query(client_cases: list[dict] | None = None) -> None:
    """Sync backend + optional client overlay cases into RAG before search."""
    rag_store.sync_all_cases()
    if client_cases:
        indexed = rag_store.index_client_cases(client_cases)
        if indexed:
            logger.info("Copilot RAG indexed %s client overlay case(s)", indexed)
