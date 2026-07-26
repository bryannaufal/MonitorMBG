"""LLM response synthesizer for the AI Copilot (Kimi + RAG)."""

from __future__ import annotations

import logging
from typing import Any, AsyncGenerator

import httpx

from app import demo_data, seed_data as sd
from app.config import settings
from app.services.copilot.retriever import retriever

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Anda adalah Asisten Ringkasan Kasus MonitorMBG — asisten inteligen untuk operator
pemerintah yang mengawasi program Makan Bergizi Gratis (MBG).

Peran Anda:
- Menyintesis informasi dari kasus, sinyal, bukti, dan laporan
- Membantu operator mengidentifikasi pola, anomali, dan isu prioritas
- Memberikan rekomendasi berbasis data untuk investigasi
- Menjawab pertanyaan tentang wilayah, sekolah, vendor, atau kasus tertentu

Aturan:
- Hanya gunakan konteks yang diberikan; jika tidak cukup, katakan apa yang masih perlu diverifikasi
- Selalu sebut sumber/kasus yang Anda rujuk
- Ringkas, operasional, Bahasa Indonesia
- Ini sinyal pra-verifikasi — bukan keputusan final"""


def _chat_base_url() -> str:
    return (settings.KIMI_BASE_URL or "https://api.kimi.com/coding/v1").rstrip("/")


def _format_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    formatted: list[dict[str, Any]] = []
    for src in sources:
        meta = src.get("metadata") or {}
        formatted.append(
            {
                "title": meta.get("title") or src.get("id") or "Sumber",
                "content_snippet": (src.get("content") or src.get("text") or "")[:240],
                "source_type": meta.get("source_type") or "case",
                "source_id": meta.get("case_id") or src.get("id") or "",
                "relevance_score": float(src.get("relevance_score") or 0.0),
            }
        )
    return formatted


def _fallback_answer(query: str, conversation_id: str | None) -> dict[str, Any]:
    return demo_data.copilot_answer(query, conversation_id)


def _answer_from_retrieval(query: str, retrieved: list[dict[str, Any]]) -> str:
    """Synthesize a direct answer from RAG hits when Kimi is unavailable."""
    lines = ["Berdasarkan kasus terindeks dalam sistem:"]
    for doc in retrieved[:5]:
        meta = doc.get("metadata") or {}
        title = meta.get("title") or doc.get("id") or "Kasus"
        snippet = (doc.get("content") or doc.get("text") or "").split("\n")[0][:220]
        lines.append(f"- **{title}**: {snippet}")
    lines.append(
        "\nJawaban di atas merujuk konteks kasus internal (termasuk kasus runtime bila sudah di-index). "
        "Verifikasi operator tetap diperlukan."
    )
    return "\n".join(lines)


async def _kimi_chat(user_content: str) -> str | None:
    api_key = (settings.KIMI_API_KEY or "").strip()
    if not api_key:
        return None

    body: dict[str, Any] = {
        "model": settings.KIMI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    }
    base = _chat_base_url()
    if "moonshot" in base:
        body["temperature"] = 0.3

    url = f"{base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=settings.KIMI_TIMEOUT_SECONDS) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            payload = resp.json()
        choices = payload.get("choices") or []
        if not choices:
            return None
        return ((choices[0].get("message") or {}).get("content") or "").strip() or None
    except Exception as exc:
        logger.warning("Copilot Kimi chat failed: %s", exc)
        return None


class Synthesizer:
    def __init__(self, model: str | None = None):
        self.model = model or settings.KIMI_MODEL

    async def generate(
        self,
        query: str,
        filters: dict | None = None,
        conversation_id: str | None = None,
        client_cases: list[dict] | None = None,
    ) -> dict[str, Any]:
        from app.services.copilot.service import prepare_copilot_query

        prepare_copilot_query(client_cases)

        retrieved = retriever.retrieve(query, filters)
        if not retrieved:
            return _fallback_answer(query, conversation_id)

        context = retriever.retrieve_with_context(query, filters)
        user_prompt = (
            f"Konteks kasus (RAG):\n{context}\n\n"
            f"Pertanyaan operator:\n{query}\n\n"
            "Jawab berdasarkan konteks di atas. Jika kasus yang dimaksud ada di konteks, sebut nomor dan judulnya."
        )

        answer = await _kimi_chat(user_prompt)
        sources = _format_sources(retrieved)
        confidence = round(
            sum(s["relevance_score"] for s in sources) / max(len(sources), 1),
            2,
        )

        if not answer:
            answer = _answer_from_retrieval(query, retrieved)
            if sd.GOVERNANCE_NOTICE not in answer:
                answer = f"{answer}\n\n{sd.GOVERNANCE_NOTICE}"
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "conversation_id": conversation_id or "copilot-session",
            }

        if sd.GOVERNANCE_NOTICE not in answer:
            answer = f"{answer}\n\n{sd.GOVERNANCE_NOTICE}"

        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "conversation_id": conversation_id or "copilot-session",
        }

    async def generate_stream(
        self,
        query: str,
        filters: dict | None = None,
        conversation_id: str | None = None,
        client_cases: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        result = await self.generate(query, filters, conversation_id, client_cases)
        for token in result["answer"].split():
            yield token + " "


synthesizer = Synthesizer()
