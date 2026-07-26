"""Test fusion pada jalur CREATE CASE: kandidat yang dicentang ikut diproses.

Menutup celah bug: POST /signals/{id}/review dengan ``decision="create"`` dan
``selected_signal_ids`` terisi sebelumnya hanya menautkan sinyal asal —
kandidat terkait (mis. sinyal media sosial #20) diabaikan, sehingga lampiran
kandidat (26.jpg) tidak menjadi bukti kasus dan statusnya tidak berubah.

Setiap test berjalan pada state runtime bersih: modul seed/demo/review store
di-reload sebelum dan sesudah test agar mutasi tidak bocor antar-test.
"""

import importlib

import pytest
from httpx import ASGITransport, AsyncClient

from app import demo_data as demo_data_module
from app import review_store as review_store_module
from app import seed_data as seed_data_module
from app.main import app

_RUNTIME_MODULES = (seed_data_module, demo_data_module, review_store_module)


@pytest.fixture(autouse=True)
def reset_runtime_state():
    for module in _RUNTIME_MODULES:
        importlib.reload(module)
    yield
    for module in _RUNTIME_MODULES:
        importlib.reload(module)


async def make_client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def create_payload(**overrides):
    """Payload realistis seperti dikirim halaman review saat #20 dicentang."""
    payload = {
        "decision": "create",
        "searched_related": True,
        "selected_signal_ids": [20],
        "selected_evidence_ids": [],
        "new_case": {
            "title": "Dugaan kontaminasi makanan pada SDN 1 Karang Agung",
            "issue_category": "dugaan keamanan pangan",
            "region": "Lampung",
            "district": "Kabupaten Tanggamus",
            "school": "SDN 1 Karang Agung",
            "vendor_id": "vnd-unknown",
        },
        "assignment": {
            "investigator": "Operator Pengawasan Tanggamus",
            "unit": "Dinas Kesehatan Kabupaten Tanggamus",
            "urgency": "Kritis",
            "sla": "24h",
            "reviewer_note": "",
            "recommended_action": "Jadwalkan verifikasi lapangan segera dan minta klarifikasi penyedia makanan.",
        },
        "override": {
            "operator_adjusted": True,
            "priority_label": "Kritis",
            "final_priority_score": 82,
            "override_reason": "kanal resmi + lokasi spesifik + lampiran",
        },
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_case_with_selected_signal_fuses_fully():
    """E.1-E.4: create dari #19 dengan #20 dicentang menautkan keduanya + bukti."""
    async with await make_client() as client:
        # Guard awal: keduanya belum terhubung dan 26.jpg belum jadi bukti kasus.
        assert (await client.get("/api/v1/signals/19")).json()["case_id"] is None
        assert (await client.get("/api/v1/signals/20")).json()["case_id"] is None

        res = await client.post("/api/v1/signals/19/review", json=create_payload())
        assert res.status_code == 200
        data = res.json()
        assert data["outcome"] == "created"
        cid = data["case_id"]
        assert data["case"]["status"] == "Open & Monitored"
        assert data["case"]["handling_strategy"] == "direct"

        # E.1 — response memuat kasus baru + daftar sinyal/bukti hasil fusion.
        assert data["linked_signal_ids"] == [19, 20]
        assert len(data["added_evidence_ids"]) == 2
        snap = data["case"]
        assert snap["case_id"] == cid
        assert {s["id"] for s in snap["signals"]} == {19, 20}
        paths = {e["file_path"] for e in snap["evidence"]}
        assert any(p.endswith("/4.jpg") for p in paths)
        assert any(p.endswith("/26.jpg") for p in paths)
        types = {e["event_type"] for e in snap["audit_events"]}
        assert {"case_created", "signal_merged", "evidence_added", "social_signal_reviewed"} <= types

        # #19 dan #20 sama-sama terhubung ke case_id baru, status berubah.
        sig19 = (await client.get("/api/v1/signals/19")).json()
        sig20 = (await client.get("/api/v1/signals/20")).json()
        assert sig19["case_id"] == cid and sig19["status"] == "Terhubung ke Kasus"
        assert sig20["case_id"] == cid and sig20["status"] == "Terhubung ke Kasus"
        assert sig20["issue_category"] == "dugaan keamanan pangan"

        # E.2 — GET detail kasus memuat kedua bukti + audit lengkap.
        detail = (await client.get(f"/api/v1/cases/{cid}")).json()
        detail_paths = {e["file_path"] for e in detail["evidence"]}
        assert any(p.endswith("/4.jpg") for p in detail_paths)
        assert any(p.endswith("/26.jpg") for p in detail_paths)
        assert detail["signals_count"] == 2
        assert detail["evidence_count"] == 2
        detail_types = {e["event_type"] for e in detail["audit_events"]}
        assert {"case_created", "signal_merged", "evidence_added", "social_signal_reviewed"} <= detail_types
        # Bukti 26.jpg tetap bukti pra-verifikasi dari media sosial.
        social_ev = next(e for e in detail["evidence"] if e["file_path"].endswith("/26.jpg"))
        assert social_ev["review_status"] == "Perlu Ditinjau"
        assert social_ev["source"] == "Media Sosial"
        assert social_ev["signal_id"] == 20

        # E.3 — filter "Perlu Tindakan" (unlinked) tidak lagi memuat #20/#19.
        unlinked = (await client.get("/api/v1/signals?linked=unlinked")).json()["items"]
        assert all(s["id"] not in {19, 20} for s in unlinked)

        # E.4 — filter "Terhubung ke Kasus" (linked) memuat #20 dengan case baru.
        linked = (await client.get("/api/v1/signals?linked=linked")).json()["items"]
        sig20_linked = next((s for s in linked if s["id"] == 20), None)
        assert sig20_linked is not None and sig20_linked["case_id"] == cid


@pytest.mark.asyncio
async def test_case_lifecycle_is_independent_from_child_ticket_status():
    """Closing a workstream does not close the case; closure needs verification."""
    async with await make_client() as client:
        created = (await client.post(
            "/api/v1/signals/19/review",
            json=create_payload(selected_signal_ids=[], selected_evidence_ids=[]),
        )).json()
        cid = created["case_id"]
        ticket_response = await client.post(
            f"/api/v1/cases/{cid}/tickets",
            json={"title": "Verifikasi lapangan", "workstream": "Lapangan"},
        )
        assert ticket_response.status_code == 200
        ticket = ticket_response.json()["ticket"]
        assert ticket_response.json()["case"]["tickets"][0]["id"] == ticket["id"]

        # "Baru" cannot jump straight to "Selesai"; work is picked up first.
        assert (await client.patch(f"/api/v1/tickets/{ticket['id']}/status",
                                   json={"status": "Selesai"})).status_code == 422
        assert (await client.patch(f"/api/v1/tickets/{ticket['id']}/status",
                                   json={"status": "Sedang Ditinjau"})).status_code == 200
        updated_ticket = await client.patch(f"/api/v1/tickets/{ticket['id']}/status", json={"status": "Selesai"})
        assert updated_ticket.status_code == 200
        detail = (await client.get(f"/api/v1/cases/{cid}")).json()
        assert detail["status"] == "Open & Monitored"

        rejected = await client.patch(f"/api/v1/cases/{cid}", json={"status": "Closed"})
        assert rejected.status_code == 422
        closed = await client.patch(
            f"/api/v1/cases/{cid}",
            json={"status": "Closed", "resolution_summary": "Verifikasi lapangan mengonfirmasi tindakan perbaikan."},
        )
        assert closed.status_code == 200
        assert closed.json()["case"]["status"] == "Closed"


@pytest.mark.asyncio
async def test_create_case_without_selection_leaves_candidate_untouched():
    """E.5 regression: create tanpa mencentang #20 tidak menautkan #20/26.jpg."""
    async with await make_client() as client:
        mbg001_before = (await client.get("/api/v1/cases/case-001")).json()

        res = await client.post(
            "/api/v1/signals/19/review",
            json=create_payload(selected_signal_ids=[], selected_evidence_ids=[]),
        )
        assert res.status_code == 200
        data = res.json()
        cid = data["case_id"]
        assert data["linked_signal_ids"] == [19]

        # Hanya lampiran sinyal asal yang menjadi bukti.
        paths = {e["file_path"] for e in data["case"]["evidence"]}
        assert any(p.endswith("/4.jpg") for p in paths)
        assert not any(p.endswith("/26.jpg") for p in paths)

        # #20 tetap pada antrean Perlu Tindakan.
        sig20 = (await client.get("/api/v1/signals/20")).json()
        assert sig20["case_id"] is None and sig20["status"] == "Belum Dibentuk Kasus"
        unlinked = (await client.get("/api/v1/signals?linked=unlinked")).json()["items"]
        assert any(s["id"] == 20 for s in unlinked)
        detail = (await client.get(f"/api/v1/cases/{cid}")).json()
        assert all(not e["file_path"].endswith("/26.jpg") for e in detail["evidence"])

        # Seed MBG-001 tidak berubah akibat fusion.
        mbg001_after = (await client.get("/api/v1/cases/case-001")).json()
        assert mbg001_after["case_number"] == "MBG-001"
        assert {e["id"] for e in mbg001_after["evidence"]} == {e["id"] for e in mbg001_before["evidence"]}


@pytest.mark.asyncio
async def test_create_with_already_linked_candidate_is_idempotent():
    """D: kandidat yang sudah terhubung dilewati — tanpa relasi/evidence ganda."""
    async with await make_client() as client:
        first = (await client.post("/api/v1/signals/19/review", json=create_payload())).json()
        cid_a = first["case_id"]

        # Kasus kedua dari sinyal lain, tetap mencentang #20 yang SUDAH terhubung.
        second = await client.post(
            "/api/v1/signals/17/review",
            json={
                "decision": "create",
                "searched_related": True,
                "selected_signal_ids": [20],
                "new_case": {"title": "Kasus uji idempotensi", "issue_category": "porsi protein kurang"},
            },
        )
        assert second.status_code == 200
        cid_b = second.json()["case_id"]

        # #20 tetap menunjuk kasus pertama; kasus kedua tidak menyerap #20/26.jpg.
        sig20 = (await client.get("/api/v1/signals/20")).json()
        assert sig20["case_id"] == cid_a
        detail_b = (await client.get(f"/api/v1/cases/{cid_b}")).json()
        assert {s["id"] for s in detail_b["signals"]} == {17}
        assert all(not e["file_path"].endswith("/26.jpg") for e in detail_b["evidence"])

        # Kasus pertama hanya punya satu bukti 26.jpg (tanpa duplikasi).
        detail_a = (await client.get(f"/api/v1/cases/{cid_a}")).json()
        assert sum(1 for e in detail_a["evidence"] if e["file_path"].endswith("/26.jpg")) == 1
        assert {s["id"] for s in detail_a["signals"]} == {19, 20}


@pytest.mark.asyncio
async def test_create_with_unknown_candidate_fails_without_partial_state():
    """D: ID kandidat tak dikenal -> 422 dan tidak ada status partial."""
    async with await make_client() as client:
        cases_before = (await client.get("/api/v1/cases")).json()["total"]

        res = await client.post(
            "/api/v1/signals/19/review",
            json=create_payload(selected_signal_ids=[99999]),
        )
        assert res.status_code == 422

        # Tidak ada kasus baru; #19 dan #20 tidak berubah sama sekali.
        assert (await client.get("/api/v1/cases")).json()["total"] == cases_before
        sig19 = (await client.get("/api/v1/signals/19")).json()
        sig20 = (await client.get("/api/v1/signals/20")).json()
        assert sig19["case_id"] is None and sig19["status"] == "Belum Dibentuk Kasus"
        assert sig20["case_id"] is None and sig20["status"] == "Belum Dibentuk Kasus"


@pytest.mark.asyncio
async def test_merge_path_still_works_and_fuses_selected_candidates():
    """E.5 regression: jalur merge tetap bekerja, termasuk kandidat terpilih."""
    async with await make_client() as client:
        # Bentuk kasus dari #19 tanpa kandidat.
        created = (await client.post(
            "/api/v1/signals/19/review",
            json=create_payload(selected_signal_ids=[], selected_evidence_ids=[]),
        )).json()
        cid = created["case_id"]

        # Merge sinyal #18 ke kasus itu sambil mencentang #20 sebagai pendukung.
        merged = await client.post(
            "/api/v1/signals/18/review",
            json={
                "decision": "merge",
                "searched_related": True,
                "target_case_id": cid,
                "selected_signal_ids": [20],
                "assignment": {"investigator": "Operator Pengawasan Tanggamus"},
            },
        )
        assert merged.status_code == 200
        data = merged.json()
        assert data["outcome"] == "merged" and data["case_id"] == cid
        assert data["linked_signal_ids"] == [18, 20]

        # Ketiga sinyal tertaut; 4.jpg & 26.jpg ada tepat satu kali.
        detail = (await client.get(f"/api/v1/cases/{cid}")).json()
        assert {s["id"] for s in detail["signals"]} == {19, 20, 18}
        paths = [e["file_path"] for e in detail["evidence"]]
        assert sum(1 for p in paths if p.endswith("/4.jpg")) == 1
        assert sum(1 for p in paths if p.endswith("/26.jpg")) == 1
        types = {e["event_type"] for e in detail["audit_events"]}
        assert {"case_created", "signal_merged", "evidence_added"} <= types

        # #20 tidak lagi pada antrean Perlu Tindakan.
        unlinked = (await client.get("/api/v1/signals?linked=unlinked")).json()["items"]
        assert all(s["id"] != 20 for s in unlinked)
