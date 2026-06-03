"""LLM response synthesizer for the AI Copilot."""

from typing import Any, AsyncGenerator

from app.services.copilot.retriever import retriever

# TODO: Uncomment when openai is configured
# from openai import AsyncOpenAI


SYSTEM_PROMPT = """You are the MonitorMBG AI Copilot — an intelligent assistant for government 
operators overseeing the Makan Bergizi Gratis (Free Nutritious Meals) program.

Your role:
- Synthesize information from complaints, reports, and daily field reports
- Help operators identify patterns, anomalies, and priority issues
- Provide data-driven recommendations for investigation
- Answer questions about specific regions, schools, or time periods

Always cite your sources. Be concise and actionable.
Respond in Bahasa Indonesia unless the operator writes in English."""


class Synthesizer:
    """
    LLM-powered response generator for the AI Copilot.

    Uses retrieved context (RAG) to generate informed,
    grounded responses for operator queries.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = None

    def _get_client(self):
        """Lazy-initialize the OpenAI client."""
        if self.client is None:
            pass
            # TODO: Initialize OpenAI client
            # from app.config import settings
            # self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self.client

    async def generate(
        self,
        query: str,
        filters: dict | None = None,
    ) -> dict[str, Any]:
        """
        Generate a copilot response with RAG context.

        Returns:
            {"answer": str, "sources": list, "confidence": float}
        """
        # Retrieve relevant context
        context = retriever.retrieve_with_context(query, filters)
        sources = retriever.retrieve(query, filters)

        # TODO: Call LLM with context
        # messages = [
        #     {"role": "system", "content": SYSTEM_PROMPT},
        #     {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        # ]
        # response = await self._get_client().chat.completions.create(
        #     model=self.model,
        #     messages=messages,
        # )
        # answer = response.choices[0].message.content

        answer = f"[Copilot placeholder] Received query: {query}"

        return {
            "answer": answer,
            "sources": sources,
            "confidence": 0.0,
        }

    async def generate_stream(
        self,
        query: str,
        filters: dict | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a copilot response token-by-token for real-time rendering.
        """
        context = retriever.retrieve_with_context(query, filters)

        # TODO: Implement streaming with OpenAI
        # messages = [
        #     {"role": "system", "content": SYSTEM_PROMPT},
        #     {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        # ]
        # stream = await self._get_client().chat.completions.create(
        #     model=self.model, messages=messages, stream=True
        # )
        # async for chunk in stream:
        #     if chunk.choices[0].delta.content:
        #         yield chunk.choices[0].delta.content

        # Placeholder streaming
        for word in f"Placeholder response for: {query}".split():
            yield word + " "


# ── Singleton ──
synthesizer = Synthesizer()
