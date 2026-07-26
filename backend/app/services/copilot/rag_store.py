"""In-memory copilot RAG store — Gemini embeddings + local fallback + JSON cache."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.copilot.embedder import (
    EmbeddingError,
    LOCAL_EMBED_DIM,
    LOCAL_EMBED_LABEL,
    active_embedding_model,
    cosine_similarity,
    embed_text,
)
from app.services.copilot.indexer import (
    build_case_document,
    build_case_document_from_payload,
    document_metadata,
    metadata_from_case,
)

logger = logging.getLogger(__name__)

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "data" / "copilot_rag_fixture.json"
_CASE_REF_RE = re.compile(r"(?:mbg[-\s]?(\d{3})|case[-\s]?(\d{3}))", re.IGNORECASE)
_TOKEN_RE = re.compile(r"[a-z0-9]{3,}", re.IGNORECASE)


@dataclass
class RAGDocument:
    id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding_engine: str = ""


class CopilotRAGStore:
    def __init__(self) -> None:
        self._docs: dict[str, RAGDocument] = {}
        self._loaded_fixture = False
        self.embedding_engine: str = active_embedding_model()

    def __len__(self) -> int:
        return len(self._docs)

    def clear(self) -> None:
        self._docs.clear()
        self._loaded_fixture = False

    def upsert(self, doc: RAGDocument) -> None:
        self._docs[doc.id] = doc

    def has_case(self, case_id: str) -> bool:
        return f"case:{case_id}" in self._docs

    def _fixture_matches(self, payload: dict[str, Any]) -> bool:
        return payload.get("embedding_model") == active_embedding_model()

    def load_fixture(self, *, force: bool = False) -> int:
        if self._loaded_fixture and not force:
            return len(self._docs)
        if not FIXTURE_PATH.is_file():
            logger.info("Copilot RAG fixture not found at %s", FIXTURE_PATH)
            self._loaded_fixture = True
            return 0

        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        if not self._fixture_matches(payload):
            logger.info(
                "Copilot RAG fixture stale (model=%s, expected=%s)",
                payload.get("embedding_model"),
                active_embedding_model(),
            )
            self._loaded_fixture = True
            return 0

        self.embedding_engine = payload.get("embedding_model") or active_embedding_model()
        count = 0
        for row in payload.get("documents") or []:
            doc_id = row.get("id")
            text = row.get("text")
            embedding = row.get("embedding")
            if not doc_id or not text or not embedding:
                continue
            self.upsert(
                RAGDocument(
                    id=doc_id,
                    text=text,
                    embedding=[float(x) for x in embedding],
                    metadata=row.get("metadata") or {},
                    embedding_engine=self.embedding_engine,
                )
            )
            count += 1
        self._loaded_fixture = True
        logger.info("Copilot RAG loaded %s documents from fixture", count)
        return count

    def save_fixture(self) -> None:
        FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "embedding_model": self.embedding_engine,
            "embedding_dim": len(next(iter(self._docs.values())).embedding)
            if self._docs
            else (settings.GEMINI_EMBEDDING_DIM if active_embedding_model() != LOCAL_EMBED_LABEL else LOCAL_EMBED_DIM),
            "documents": [
                {
                    "id": d.id,
                    "text": d.text,
                    "embedding": d.embedding,
                    "metadata": d.metadata,
                }
                for d in self._docs.values()
            ],
        }
        FIXTURE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def index_case(self, case_id: str) -> bool:
        text = build_case_document(case_id)
        if not text:
            return False
        try:
            vector, engine = embed_text(text)
        except EmbeddingError as exc:
            logger.warning("Copilot RAG skip %s: %s", case_id, exc)
            return False
        self.embedding_engine = engine
        doc_id = f"case:{case_id}"
        self.upsert(
            RAGDocument(
                id=doc_id,
                text=text,
                embedding=vector,
                metadata=document_metadata(case_id),
                embedding_engine=engine,
            )
        )
        logger.info("Copilot RAG indexed %s (engine=%s)", doc_id, engine)
        return True

    def index_case_payload(self, case: dict[str, Any]) -> bool:
        """Index/update a case from a full case dict (runtime or client overlay)."""
        case_id = case.get("case_id")
        if not case_id:
            return False
        text = build_case_document_from_payload(case)
        if not text:
            return False
        try:
            vector, engine = embed_text(text)
        except EmbeddingError as exc:
            logger.warning("Copilot RAG skip payload %s: %s", case_id, exc)
            return False
        self.embedding_engine = engine
        doc_id = f"case:{case_id}"
        self.upsert(
            RAGDocument(
                id=doc_id,
                text=text,
                embedding=vector,
                metadata=metadata_from_case(case),
                embedding_engine=engine,
            )
        )
        logger.info("Copilot RAG indexed payload %s", doc_id)
        return True

    def sync_all_cases(self) -> int:
        """Ensure every in-memory case is indexed before search."""
        from app import seed_data as sd

        added = 0
        for case in sd.CASES:
            cid = case["case_id"]
            if not self.has_case(cid):
                if self.index_case(cid):
                    added += 1
        if added:
            logger.info("Copilot RAG synced %s new runtime case(s)", added)
        return added

    def index_client_cases(self, cases: list[dict[str, Any]]) -> int:
        """Index cases supplied by the frontend overlay (session-only)."""
        count = 0
        for case in cases:
            if self.index_case_payload(case):
                count += 1
        return count

    @staticmethod
    def _case_ids_from_query(query_text: str) -> list[str]:
        ids: list[str] = []
        for m in _CASE_REF_RE.finditer(query_text):
            num = m.group(1) or m.group(2)
            if num:
                ids.append(f"case-{num}")
        return ids

    def _keyword_hits(self, query_text: str, *, filter_metadata: dict | None) -> list[tuple[float, RAGDocument]]:
        q = query_text.lower()
        tokens = [t for t in _TOKEN_RE.findall(q) if len(t) >= 4]
        hits: list[tuple[float, RAGDocument]] = []
        for doc in self._docs.values():
            if filter_metadata and not all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                continue
            hay = doc.text.lower()
            meta_title = str(doc.metadata.get("title") or "").lower().replace("-", "")
            score = 0.0
            q_compact = q.replace("-", "").replace(" ", "")
            if meta_title and meta_title in q_compact:
                score = 1.0
            else:
                for tok in tokens:
                    if tok in hay:
                        score += 0.12
            if score > 0:
                hits.append((min(0.99, score), doc))
        hits.sort(key=lambda item: item[0], reverse=True)
        return hits

    def _doc_result(self, doc: RAGDocument, score: float) -> dict[str, Any]:
        return {
            "id": doc.id,
            "text": doc.text,
            "metadata": doc.metadata,
            "distance": 1.0 - score,
            "relevance_score": round(score, 4),
        }

    def _merge_results(self, ranked: list[tuple[float, RAGDocument]], top_k: int) -> list[dict[str, Any]]:
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for score, doc in ranked:
            if doc.id in seen:
                continue
            seen.add(doc.id)
            out.append(self._doc_result(doc, score))
            if len(out) >= top_k:
                break
        return out

    def _sync_seed_to_fixture(self) -> None:
        from app import seed_data as sd

        missing = [c["case_id"] for c in sd.CASES if not self.has_case(c["case_id"])]
        if not missing:
            return
        for cid in missing:
            self.index_case(cid)
        if self._docs:
            self.save_fixture()
            logger.info(
                "Copilot RAG fixture synced from seed → %s (%s docs)",
                FIXTURE_PATH.name,
                len(self._docs),
            )

    def bootstrap(self) -> None:
        from app import seed_data as sd

        self.load_fixture()
        seed_ids = [c["case_id"] for c in sd.CASES]
        missing_seed = [cid for cid in seed_ids if not self.has_case(cid)]

        if missing_seed:
            for cid in missing_seed:
                self.index_case(cid)
            if (settings.SCRAPER_MODE or "fixture").lower() == "fixture" and self._docs:
                self.save_fixture()

        if self._docs:
            logger.info("Copilot RAG ready — %s documents (%s)", len(self._docs), self.embedding_engine)
        else:
            logger.warning("Copilot RAG empty — tidak ada kasus seed ter-index")

    def query(
        self,
        query_text: str,
        *,
        n_results: int | None = None,
        filter_metadata: dict | None = None,
    ) -> list[dict[str, Any]]:
        self.sync_all_cases()
        if not self._docs:
            return []

        top_k = n_results or settings.COPILOT_TOP_K
        ranked: list[tuple[float, RAGDocument]] = []

        for cid in self._case_ids_from_query(query_text):
            doc = self._docs.get(f"case:{cid}")
            if doc:
                if not filter_metadata or all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                    ranked.append((1.0, doc))

        ranked.extend(self._keyword_hits(query_text, filter_metadata=filter_metadata))

        try:
            q_vec, _ = embed_text(query_text)
            for doc in self._docs.values():
                if filter_metadata and not all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                    continue
                sim = cosine_similarity(q_vec, doc.embedding)
                if sim > 0:
                    ranked.append((sim, doc))
        except EmbeddingError as exc:
            logger.warning("Copilot RAG query embed failed: %s", exc)
            if not ranked:
                return []

        ranked.sort(key=lambda item: item[0], reverse=True)
        return self._merge_results(ranked, top_k)


rag_store = CopilotRAGStore()
