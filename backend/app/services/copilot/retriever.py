"""RAG retriever — semantic search over case data and documents."""

from typing import Any

from app.services.copilot.vector_store import vector_store


class Retriever:
    """
    Retrieves relevant documents from the vector store
    based on semantic similarity to operator queries.
    """

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    def retrieve(
        self,
        query: str,
        filters: dict | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Operator's natural language query
            filters: Optional metadata filters (region, date, type)

        Returns:
            List of relevant documents with scores
        """
        results = vector_store.query(
            query_text=query,
            n_results=self.top_k,
            filter_metadata=filters,
        )

        return [
            {
                "id": r.get("id", ""),
                "content": r.get("text", ""),
                "metadata": r.get("metadata", {}),
                "relevance_score": 1 - r.get("distance", 1),  # Convert distance to similarity
            }
            for r in results
        ]

    def retrieve_with_context(
        self,
        query: str,
        filters: dict | None = None,
    ) -> str:
        """
        Retrieve and format context for LLM consumption.

        Returns a formatted context string ready for prompt injection.
        """
        documents = self.retrieve(query, filters)

        if not documents:
            return "No relevant documents found."

        context_parts = []
        for i, doc in enumerate(documents, 1):
            source_type = doc["metadata"].get("source_type", "unknown")
            context_parts.append(
                f"[Source {i} ({source_type})]:\n{doc['content']}\n"
            )

        return "\n---\n".join(context_parts)


# ── Singleton ──
retriever = Retriever()
