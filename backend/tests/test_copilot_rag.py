"""Copilot RAG tests — Gemini (mocked) + local fallback."""

import hashlib

import pytest

from app.config import settings
from app.services.copilot.embedder import (
    LOCAL_EMBED_DIM,
    LOCAL_EMBED_LABEL,
    cosine_similarity,
    embed_text,
    gemini_embeddings_available,
    local_embed,
)
from app.services.copilot.rag_store import rag_store
from app.services.copilot.service import index_case_for_copilot, reindex_all_cases

DIM = 768


def _fake_vector(text: str) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    while len(values) < DIM:
        for i in range(0, len(digest), 4):
            chunk = digest[i : i + 4]
            if len(chunk) < 4:
                break
            values.append(int.from_bytes(chunk, "big") / 2**32)
        digest = hashlib.sha256(digest).digest()
    return values[:DIM]


@pytest.fixture(autouse=True)
def mock_gemini_embed(monkeypatch, request):
    if request.node.get_closest_marker("no_gemini_mock"):
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        return

    def fake_embed_batch(texts: list[str]):
        return [_fake_vector(t) for t in texts]

    monkeypatch.setattr("app.services.copilot.embedder._gemini_embed_batch", fake_embed_batch)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-key")


def test_local_embed_deterministic():
    a = local_embed("mbg protein rendah")
    b = local_embed("mbg protein rendah")
    c = local_embed("vendor watchlist")
    assert len(a) == LOCAL_EMBED_DIM
    assert a == b
    assert cosine_similarity(a, c) < cosine_similarity(a, b)


@pytest.mark.no_gemini_mock
def test_embed_text_local_without_gemini_key():
    vec, engine = embed_text("contoh teks kasus gizi")
    assert len(vec) == LOCAL_EMBED_DIM
    assert engine == LOCAL_EMBED_LABEL


def test_embed_text_uses_gemini_model():
    vec, engine = embed_text("contoh teks")
    assert len(vec) == DIM
    assert engine == settings.GEMINI_EMBEDDING_MODEL


def test_gemini_embeddings_available_with_key(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    assert gemini_embeddings_available() is False
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "AIza-test")
    assert gemini_embeddings_available() is True


def test_rag_fixture_bootstrap():
    rag_store.clear()
    rag_store.bootstrap()
    assert len(rag_store) >= 10
    assert rag_store.has_case("case-001")


@pytest.mark.no_gemini_mock
def test_rag_bootstrap_local_without_gemini():
    rag_store.clear()
    rag_store.bootstrap()
    assert len(rag_store) >= 10
    assert rag_store.embedding_engine == LOCAL_EMBED_LABEL


def test_rag_query_returns_case():
    rag_store.clear()
    rag_store.bootstrap()
    hits = rag_store.query("kasus prioritas tinggi protein gizi", n_results=5)
    assert hits
    assert all(h.get("metadata", {}).get("case_id") for h in hits)


def test_index_runtime_case():
    from app import seed_data as sd

    rag_store.clear()
    rag_store.bootstrap()
    before = len(rag_store)
    cid = "case-999"
    sd.CASES.append({
        "case_id": cid,
        "vendor_id": "vnd-001",
        "school": "SDN Test",
        "issue_category": "gizi",
        "priority_label": "Tinggi",
        "status": "Sedang Ditinjau",
        "title": "Kasus uji RAG",
        "created_at": "2026-07-26T00:00:00Z",
        "updated_at": "2026-07-26T00:00:00Z",
    })
    sd.CASE_BY_ID[cid] = sd.CASES[-1]
    sd.RISK_BY_CASE[cid] = {
        "id": 999,
        "case_id": cid,
        "vendor_id": "vnd-001",
        "vendor_name": "Vendor Test",
        "region": "Jakarta",
        "severity_score": 70,
        "confidence_score": 60,
        "actionability_score": 55,
        "nutrition_score": 50,
        "final_priority_score": 65,
        "priority_label": "Tinggi",
        "explanation": "Kasus uji",
        "recommended_action": "Verifikasi",
        "computed_at": "2026-07-26T00:00:00Z",
        "ai_notice": sd.GOVERNANCE_NOTICE,
    }
    try:
        index_case_for_copilot(cid)
        assert len(rag_store) == before + 1
        assert rag_store.has_case(cid)
    finally:
        sd.CASES[:] = [c for c in sd.CASES if c["case_id"] != cid]
        sd.CASE_BY_ID.pop(cid, None)
        sd.RISK_BY_CASE.pop(cid, None)
        reindex_all_cases()


def test_rag_finds_case_by_number():
    rag_store.clear()
    rag_store.bootstrap()
    payload = {
        "case_id": "case-011",
        "case_number": "MBG-011",
        "title": "Tinjauan sinyal: belatung MBG Lampung",
        "status": "Sedang Ditinjau",
        "priority_label": "Sedang",
        "vendor_name": "Belum teridentifikasi",
        "region": "Lampung",
        "district": "Belum teridentifikasi",
        "school": "Belum teridentifikasi",
        "issue_category": "dugaan keamanan pangan",
        "summary": "Belatung",
        "what_happened": "Dugaan belatung",
        "why_it_matters": "Keamanan pangan",
        "recommended_action": "Verifikasi",
        "risk_explanation": "",
        "score": {"severity_score": 75, "confidence_score": 13, "actionability_score": 65, "nutrition_score": 35, "final_priority_score": 62},
    }
    rag_store.index_case_payload(payload)
    hits = rag_store.query("apakah ada MBG-011?", n_results=3)
    assert hits
    assert hits[0]["metadata"].get("case_id") == "case-011"


def test_rag_finds_belatung_keyword():
    rag_store.clear()
    rag_store.bootstrap()
    payload = {
        "case_id": "case-011",
        "case_number": "MBG-011",
        "title": "Tinjauan sinyal: belatung MBG anak SD Lampung",
        "status": "Sedang Ditinjau",
        "priority_label": "Sedang",
        "vendor_name": "Belum teridentifikasi",
        "region": "Lampung",
        "district": "Belum teridentifikasi",
        "school": "Belum teridentifikasi",
        "issue_category": "dugaan keamanan pangan",
        "summary": "Unggahan media sosial menyebut dugaan belatung",
        "what_happened": "Dugaan belatung pada MBG",
        "why_it_matters": "Keamanan pangan",
        "recommended_action": "Verifikasi lapangan",
        "risk_explanation": "",
        "score": {"severity_score": 75, "confidence_score": 13, "actionability_score": 65, "nutrition_score": 35, "final_priority_score": 62},
    }
    rag_store.index_case_payload(payload)
    hits = rag_store.query("apakah ada case belatung?", n_results=5)
    assert any("belatung" in (h.get("text") or "").lower() for h in hits)
