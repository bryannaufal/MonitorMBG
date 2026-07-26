"""Copilot vector store — delegates to in-memory RAG."""

from typing import Any

from app.services.copilot.embedder import embed_batch
from app.services.copilot.rag_store import RAGDocument, rag_store


class VectorStore:
    def initialize(self) -> None:
        rag_store.bootstrap()

    def add_documents(
        self,
        ids: list[str],
        texts: list[str],
        metadatas: list[dict] | None = None,
    ) -> None:
        vectors, engine = embed_batch(texts)
        rag_store.embedding_engine = engine
        for i, doc_id in enumerate(ids):
            rag_store.upsert(
                RAGDocument(
                    id=doc_id,
                    text=texts[i],
                    embedding=vectors[i],
                    metadata=(metadatas[i] if metadatas else {}),
                    embedding_engine=engine,
                )
            )

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[dict[str, Any]]:
        return rag_store.query(
            query_text,
            n_results=n_results,
            filter_metadata=filter_metadata,
        )

    def delete_documents(self, ids: list[str]) -> None:
        for doc_id in ids:
            rag_store._docs.pop(doc_id, None)


vector_store = VectorStore()
