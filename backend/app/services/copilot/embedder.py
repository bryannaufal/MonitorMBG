"""Text embeddings for copilot RAG — Gemini API with local hash fallback."""

from __future__ import annotations

import hashlib
import logging
import math
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

LOCAL_EMBED_LABEL = "local-fixture-v1"
LOCAL_EMBED_DIM = 256


class EmbeddingError(Exception):
    """Raised when embedding cannot be produced."""


def gemini_embeddings_available() -> bool:
    return bool((settings.GEMINI_API_KEY or "").strip())


def active_embedding_model() -> str:
    if gemini_embeddings_available():
        return settings.GEMINI_EMBEDDING_MODEL
    return LOCAL_EMBED_LABEL


def local_embed(text: str, *, dim: int = LOCAL_EMBED_DIM) -> list[float]:
    """Deterministic hash bag-of-words vector — no external API."""
    vec = [0.0] * dim
    for tok in text.lower().split():
        if not tok:
            continue
        digest = hashlib.sha256(tok.encode("utf-8")).digest()
        for i, byte in enumerate(digest):
            vec[i % dim] += (byte - 128) / 128.0
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def _model_resource() -> str:
    model = (settings.GEMINI_EMBEDDING_MODEL or "gemini-embedding-001").strip()
    return model if model.startswith("models/") else f"models/{model}"


def _embed_url(suffix: str) -> str:
    base = (settings.GEMINI_API_BASE_URL or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    model = settings.GEMINI_EMBEDDING_MODEL.replace("models/", "")
    return f"{base}/models/{model}:{suffix}"


def _request_body(text: str) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": _model_resource(),
        "content": {"parts": [{"text": text}]},
    }
    dim = settings.GEMINI_EMBEDDING_DIM
    if dim and dim > 0:
        body["outputDimensionality"] = dim
    return body


def _parse_embedding(payload: dict[str, Any]) -> list[float]:
    embedding = payload.get("embedding") or {}
    values = embedding.get("values")
    if not isinstance(values, list) or not values:
        raise EmbeddingError("Gemini embed response missing embedding.values")
    return [float(x) for x in values]


def _gemini_embed_one(text: str, *, client: httpx.Client) -> list[float]:
    api_key = (settings.GEMINI_API_KEY or "").strip()
    url = _embed_url("embedContent")
    resp = client.post(
        url,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        json=_request_body(text),
    )
    resp.raise_for_status()
    return _parse_embedding(resp.json())


def _gemini_embed_batch(texts: list[str]) -> list[list[float]]:
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        raise EmbeddingError("GEMINI_API_KEY belum di-set")

    cleaned = [(t or "").strip() or " " for t in texts]
    timeout = settings.GEMINI_TIMEOUT_SECONDS
    url = _embed_url("batchEmbedContents")
    body = {"requests": [_request_body(t) for t in cleaned]}

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                url,
                headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
                json=body,
            )
            if resp.status_code >= 400:
                raise httpx.HTTPStatusError("batch failed", request=resp.request, response=resp)
            payload = resp.json()
            embeddings = payload.get("embeddings") or []
            if len(embeddings) != len(cleaned):
                raise EmbeddingError("Gemini batch embed count mismatch")
            return [[float(x) for x in item.get("values") or []] for item in embeddings]
    except Exception as exc:
        logger.info("Gemini batch embed fallback to sequential: %s", exc)
        vectors: list[list[float]] = []
        with httpx.Client(timeout=timeout) as client:
            for text in cleaned:
                vectors.append(_gemini_embed_one(text, client=client))
        return vectors


def _local_embed_batch(texts: list[str]) -> list[list[float]]:
    cleaned = [(t or "").strip() or " " for t in texts]
    return [local_embed(t) for t in cleaned]


def embed_text(text: str) -> tuple[list[float], str]:
    """Return (vector, model_label). Uses Gemini when key set, else local hash."""
    vectors, model = embed_batch([text])
    return vectors[0], model


def embed_batch(texts: list[str]) -> tuple[list[list[float]], str]:
    if not texts:
        return [], active_embedding_model()

    if gemini_embeddings_available():
        try:
            return _gemini_embed_batch(texts), settings.GEMINI_EMBEDDING_MODEL
        except Exception as exc:
            logger.warning("Gemini embed failed (%s) — fallback ke %s", exc, LOCAL_EMBED_LABEL)
            return _local_embed_batch(texts), LOCAL_EMBED_LABEL

    logger.info("GEMINI_API_KEY kosong — Copilot RAG memakai embedding lokal (%s)", LOCAL_EMBED_LABEL)
    return _local_embed_batch(texts), LOCAL_EMBED_LABEL


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
