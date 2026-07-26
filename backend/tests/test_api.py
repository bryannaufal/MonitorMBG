from httpx import ASGITransport, AsyncClient
import pytest

from app.main import app


async def make_client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health():
    async with await make_client() as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_analytics_overview():
    async with await make_client() as client:
        response = await client.get("/api/v1/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_reports"] >= 20
    assert data["high_risk_cases"] > 0


@pytest.mark.asyncio
async def test_complaints_list_and_detail():
    async with await make_client() as client:
        response = await client.get("/api/v1/complaints")
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) >= 16

        # case_id boleh None (sinyal belum dibentuk kasus); ambil yang terhubung.
        linked = next(item for item in items if item.get("case_id"))
        detail = await client.get(f"/api/v1/complaints/{linked['id']}")
        assert detail.status_code == 200
        assert detail.json()["case_id"].startswith("case-")


@pytest.mark.asyncio
async def test_vendors_list_and_404():
    async with await make_client() as client:
        response = await client.get("/api/v1/vendors")
        assert response.status_code == 200
        assert len(response.json()["items"]) >= 8

        missing = await client.get("/api/v1/vendors/unknown")
        assert missing.status_code == 404


@pytest.mark.asyncio
async def test_scoring_rankings():
    async with await make_client() as client:
        response = await client.get("/api/v1/scoring/rankings")
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["final_priority_score"] >= items[-1]["final_priority_score"]


@pytest.mark.asyncio
async def test_cases_list_and_detail():
    async with await make_client() as client:
        response = await client.get("/api/v1/cases")
        assert response.status_code == 200
        items = response.json()["items"]
        assert items
        assert items[0]["vendor"]
        assert items[0]["score"]
        assert "complaints" in items[0]
        assert "audit_events" in items[0]

        detail = await client.get(f"/api/v1/cases/{items[0]['case_id']}")
        assert detail.status_code == 200
        data = detail.json()
        assert data["case_id"] == items[0]["case_id"]
        assert data["ticket"] is None or data["ticket"]["case_id"] == data["case_id"]


@pytest.mark.asyncio
async def test_signals_link_only_to_valid_cases():
    """Setiap signal terhubung ke kasus valid ATAU eksplisit belum dibentuk kasus."""
    async with await make_client() as client:
        cases = (await client.get("/api/v1/cases")).json()["items"]
        valid_ids = {c["case_id"] for c in cases}
        signals = (await client.get("/api/v1/signals")).json()["items"]
    assert signals
    for sig in signals:
        cid = sig.get("case_id")
        assert cid is None or cid in valid_ids, f"signal {sig['id']} menunjuk kasus tak tersedia: {cid}"
    assert any(s.get("case_id") is None for s in signals), "harus ada sinyal belum dibentuk kasus"


@pytest.mark.asyncio
async def test_unknown_case_returns_404_not_other_case():
    """Tidak ada fallback diam-diam ke kasus lain."""
    async with await make_client() as client:
        missing = await client.get("/api/v1/cases/case-999")
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_signal_review_read_endpoints():
    """GET sinyal, /related, /assessment, dan 404 sinyal tak dikenal."""
    async with await make_client() as client:
        sig = await client.get("/api/v1/signals/17")
        assert sig.status_code == 200
        assert sig.json()["case_id"] is None

        missing = await client.get("/api/v1/signals/99999")
        assert missing.status_code == 404

        rel = await client.post("/api/v1/signals/17/related", json={})
        assert rel.status_code == 200
        body = rel.json()
        assert "case_candidates" in body and "signal_candidates" in body and "evidence_candidates" in body

        assess = await client.get("/api/v1/signals/17/assessment")
        assert assess.status_code == 200
        assert 0 <= assess.json()["final_priority_score"] <= 100

        inv = await client.get("/api/v1/signals/investigators")
        assert inv.status_code == 200
        assert "Operator Dewi" in inv.json()["items"]


@pytest.mark.asyncio
async def test_assignment_options_are_geography_scoped():
    """Dropdown review hanya menampilkan kandidat yang cocok dengan registry lokasi."""
    async with await make_client() as client:
        lampung = (await client.get(
            "/api/v1/signals/assignment-options",
            params={"region": "Lampung", "district": "Kabupaten Tanggamus", "school": "SDN 1 Karang Agung"},
        )).json()
        jakarta = (await client.get(
            "/api/v1/signals/assignment-options",
            params={"region": "DKI Jakarta", "district": "Jakarta Timur"},
        )).json()
        kepri = (await client.get(
            "/api/v1/signals/assignment-options",
            params={"region": "Kepulauan Riau", "district": "Kota Batam"},
        )).json()
        legacy_investigators = (await client.get(
            "/api/v1/signals/investigators",
            params={"region": "Lampung", "district": "Kabupaten Tanggamus"},
        )).json()
        unknown = (await client.get("/api/v1/signals/assignment-options")).json()

    lampung_vendors = {item["name"] for item in lampung["vendors"]}
    assert lampung_vendors == {"SPPG Tanggamus Pangan Aman", "Dapur Lampung Lintas Kabupaten"}
    lampung_investigators = {item["name"] for item in lampung["investigators"]}
    assert "Operator Pengawasan Tanggamus" in lampung_investigators
    assert "Tim Verifikasi Lapangan Lampung" in lampung_investigators
    assert "Tim Verifikasi Lapangan Jakarta Timur" not in lampung_investigators
    lampung_units = {item["name"] for item in lampung["units"]}
    assert "Dinas Kesehatan Kabupaten Tanggamus" in lampung_units
    assert "Unit Pengawasan Vendor MBG Lampung" in lampung_units
    assert "Dinas Kesehatan Jakarta Timur" not in lampung_units
    assert "Tim Verifikasi Lapangan Jakarta Timur" not in legacy_investigators["items"]

    assert {item["name"] for item in jakarta["vendors"]} == {"SPPG Nusantara Sehat"}
    assert "Tim Verifikasi Lapangan Jakarta Timur" in {item["name"] for item in jakarta["investigators"]}
    assert {item["name"] for item in kepri["vendors"]} == {"Dapur Kepri Batam Sejahtera"}
    assert "SPPG Nusantara Sehat" not in {item["name"] for item in kepri["vendors"]}
    assert unknown["vendors"] == []
    assert unknown["vendor_message"] == "Lengkapi wilayah atau sekolah untuk menampilkan kandidat penyedia yang relevan."
    assert unknown["manual_vendor"]["id"] == "__manual__"


@pytest.mark.asyncio
async def test_manual_vendor_and_cross_region_vendor_validation():
    async with await make_client() as client:
        invalid = await client.post(
            "/api/v1/signals/17/review",
            json={
                "decision": "create",
                "new_case": {
                    "region": "Lampung", "district": "Kabupaten Tanggamus",
                    "school": "SDN 1 Karang Agung", "vendor_id": "vnd-001",
                },
            },
        )
        assert invalid.status_code == 422

        manual = await client.post(
            "/api/v1/signals/17/review",
            json={
                "decision": "create",
                "new_case": {
                    "region": "Lampung", "district": "Kabupaten Tanggamus",
                    "school": "SDN 1 Karang Agung", "vendor_id": "__manual__",
                    "vendor_name": "Penyedia dari laporan lapangan",
                    "vendor_source_note": "Formulir klarifikasi operator",
                },
                "assignment": {
                    "investigator": "Operator Pengawasan Tanggamus",
                    "unit": "Dinas Kesehatan Kabupaten Tanggamus",
                },
            },
        )
        assert manual.status_code == 200
        case = manual.json()["case"]
        assert case["vendor_id"] == "vnd-unknown"
        assert case["vendor_name"] == "Penyedia dari laporan lapangan"
        assert case["region"] == "Lampung" and case["district"] == "Kabupaten Tanggamus"
        event_types = {event["event_type"] for event in case["audit_events"]}
        assert {"vendor_entered_from_report", "location_updated", "responsible_unit_assigned"} <= event_types


@pytest.mark.asyncio
async def test_signal_review_create_case_and_audit():
    """Membentuk kasus baru dari sinyal tak terhubung; kasus baru terbuka + ada audit."""
    async with await make_client() as client:
        # signal 18 = sinyal Formulir Publik belum dibentuk kasus
        res = await client.post(
            "/api/v1/signals/18/review",
            json={
                "decision": "create",
                "searched_related": True,
                "new_case": {"title": "Kasus uji review", "issue_category": "porsi protein kurang"},
                "assignment": {"investigator": "Operator Dewi", "urgency": "Sedang", "sla": "48h"},
                "override": {"operator_adjusted": True, "priority_label": "Tinggi",
                             "final_priority_score": 70, "override_reason": "pola serupa"},
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["outcome"] == "created"
        cid = data["case_id"]

        # Sinyal kini tertaut & kasus baru terbuka.
        sig = (await client.get("/api/v1/signals/18")).json()
        assert sig["case_id"] == cid
        detail = await client.get(f"/api/v1/cases/{cid}")
        assert detail.status_code == 200
        case = detail.json()
        types = {e["event_type"] for e in case["audit_events"]}
        assert "case_created" in types and "risk_overridden" in types
        assert case["score"]["severity_score"] is not None
        assert case["score"]["confidence_score"] is not None
        assert case["score"]["final_priority_score"] == 70

        # Meninjau ulang sinyal yang sudah tertaut -> 409.
        again = await client.post("/api/v1/signals/18/review", json={"decision": "defer", "defer_reason": "x"})
        assert again.status_code == 409


@pytest.mark.asyncio
async def test_evidence_fusion_belatung_scenario():
    """Skenario fusion: laporan resmi (4.jpg) + sinyal media sosial (26.jpg)."""
    async with await make_client() as client:
        # Regression guard: attachment sosial belum menjadi evidence kasus
        # mana pun sebelum operator menyetujui fusion.
        initial_cases = (await client.get("/api/v1/cases")).json()["items"]
        assert all(
            not any(e.get("file_path", "").endswith("/26.jpg") for e in case["evidence"])
            for case in initial_cases
        )

        # Laporan resmi #19 dapat dibuka & punya lampiran 4.jpg.
        report = (await client.get("/api/v1/signals/19")).json()
        assert report["case_id"] is None
        assert report["attachment_path"].endswith("/4.jpg")
        assert report["region"] == "Lampung"

        # 1) Kandidat post Twitter/X (#20) muncul dari pencarian terkait, skor SEDANG.
        rel = (await client.post("/api/v1/signals/19/related", json={})).json()
        social = next((c for c in rel["signal_candidates"] if c["id"] == 20), None)
        assert social is not None, "sinyal media sosial harus muncul sebagai kandidat"
        assert 30 <= social["match_score"] <= 60, "skor kecocokan harus tingkat sedang, bukan sangat tinggi"
        reasons = " ".join(social["reasons"]).lower()
        assert "belatung" in reasons and "lampung" in reasons
        assert "belum terkonfirmasi" in reasons  # lokasi sekolah/kabupaten belum pasti
        assert social["attachment_path"].endswith("/26.jpg")

        # Bentuk kasus dari laporan resmi (tanpa tiket otomatis).
        created = (await client.post("/api/v1/signals/19/review", json={
            "decision": "create", "searched_related": True,
            "new_case": {"title": "Dugaan kontaminasi makanan pada SDN 1 Karang Agung",
                         "issue_category": "dugaan keamanan pangan", "school": "SDN 1 Karang Agung"},
            "assignment": {"investigator": "Operator Dewi", "urgency": "Kritis", "sla": "24h",
                           "recommended_action": "Jadwalkan verifikasi lapangan segera, amankan informasi pendukung, dan minta klarifikasi penyedia makanan."},
            "override": {"operator_adjusted": True, "priority_label": "Kritis",
                         "final_priority_score": 82, "override_reason": "kanal resmi + lokasi spesifik + lampiran"},
        })).json()
        cid = created["case_id"]
        assert any(e["file_path"].endswith("/4.jpg") for e in created["case"]["evidence"])
        detail = (await client.get(f"/api/v1/cases/{cid}")).json()
        assert detail["ticket"] is None, "tidak boleh ada tiket otomatis"
        assert any(e["file_path"].endswith("/4.jpg") for e in detail["evidence"])

        # 2) Merge sinyal media sosial -> tautkan signal + bukti 26.jpg ke kasus yang sama.
        merged = (await client.post("/api/v1/signals/20/review", json={
            "decision": "merge", "searched_related": True, "target_case_id": cid,
            "selected_signal_ids": [20],
            "assignment": {"investigator": "Operator Dewi"},
            "override": {"operator_adjusted": True, "priority_label": "Kritis",
                         "final_priority_score": 85, "override_reason": "tambahan sinyal wilayah sama"},
        })).json()
        assert merged["outcome"] == "merged" and merged["case_id"] == cid
        assert any(e["file_path"].endswith("/26.jpg") for e in merged["case"]["evidence"])

        sig20 = (await client.get("/api/v1/signals/20")).json()
        assert sig20["case_id"] == cid  # signal tertaut ke kasus yang benar

        detail2 = (await client.get(f"/api/v1/cases/{cid}")).json()
        paths = {e["file_path"] for e in detail2["evidence"]}
        assert any(p.endswith("/4.jpg") for p in paths) and any(p.endswith("/26.jpg") for p in paths)
        social_ev = next(e for e in detail2["evidence"] if e["file_path"].endswith("/26.jpg"))
        assert social_ev["title"] == "Lampiran unggahan media sosial terkait dugaan keamanan pangan"
        assert social_ev["source"] == "Media Sosial"
        assert social_ev["review_status"] == "Perlu Ditinjau"
        assert social_ev["reviewer_note"] == (
            "Sinyal pendukung dari wilayah Lampung; hubungan dengan SDN 1 Karang Agung belum "
            "terkonfirmasi dan memerlukan verifikasi operator."
        )

        # 3) Audit events terbentuk & disebut dilakukan operator (bukan otomatis).
        types = {e["event_type"] for e in detail2["audit_events"]}
        for required in ("case_created", "evidence_added", "signal_merged", "risk_reassessed"):
            assert required in types, f"audit '{required}' hilang"
        merge_ev = next(e for e in detail2["audit_events"] if e["event_type"] == "signal_merged")
        assert "operator" in merge_ev["description"].lower()
        assert merge_ev["actor"] != "Sistem"

        # 4) Tidak ada klaim otomatis bahwa kedua sinyal adalah kejadian yang sama.
        blob = " ".join(e["description"] for e in detail2["audit_events"]).lower()
        assert "belum dikonfirmasi" in blob or "belum terkonfirmasi" in blob
        assert "terbukti" not in blob and "terkonfirmasi otomatis" not in blob

        # 5) Signal #20 tidak dapat membentuk kasus baru saat masih terhubung.
        blocked = await client.post("/api/v1/signals/20/review", json={"decision": "create", "new_case": {"title": "x"}})
        assert blocked.status_code == 409

        # 6) Filter Inbox: #20 di 'linked', tidak di 'unlinked'.
        linked = (await client.get("/api/v1/signals?linked=linked")).json()["items"]
        unlinked = (await client.get("/api/v1/signals?linked=unlinked")).json()["items"]
        assert any(s["id"] == 20 for s in linked) and all(s["id"] != 20 for s in unlinked)

        # 7) Unlink dengan alasan -> #20 kembali Perlu Ditinjau; audit dicatat.
        unlink = (await client.post("/api/v1/signals/20/unlink", json={"reason": "lokasi belum terkonfirmasi"})).json()
        assert unlink["outcome"] == "unlinked"
        assert {"signal_unlinked", "evidence_unlinked"} <= {e["event_type"] for e in unlink["audit_events"]}
        sig20b = (await client.get("/api/v1/signals/20")).json()
        assert sig20b["case_id"] is None and sig20b["status"] == "Perlu Ditinjau"

        # 8) 26.jpg dilepas dari kasus, 4.jpg tetap; baris/aset bukti TIDAK dihapus.
        detail3 = (await client.get(f"/api/v1/cases/{cid}")).json()
        paths3 = {e["file_path"] for e in detail3["evidence"]}
        assert any(p.endswith("/4.jpg") for p in paths3) and not any(p.endswith("/26.jpg") for p in paths3)
        all_ev = (await client.get("/api/v1/evidence?size=100")).json()["items"]
        assert any(e.get("file_path", "").endswith("/26.jpg") for e in all_ev)
        # #20 kembali ke antrean 'unlinked'.
        unlinked2 = (await client.get("/api/v1/signals?linked=unlinked")).json()["items"]
        assert any(s["id"] == 20 for s in unlinked2)
        # Unlink lagi -> 409.
        again = await client.post("/api/v1/signals/20/unlink", json={"reason": "x"})
        assert again.status_code == 409


@pytest.mark.asyncio
async def test_copilot_chat():
    async with await make_client() as client:
        response = await client.post(
            "/api/v1/copilot/chat",
            json={"message": "Kasus mana yang prioritas tertinggi?"},
        )
    assert response.status_code == 200
    data = response.json()
    # Catatan tata kelola Bahasa Indonesia selalu disertakan.
    assert "operator berwenang" in data["answer"].lower()
    assert data["sources"]


@pytest.mark.asyncio
async def test_unlink_requires_reason():
    async with await make_client() as client:
        # #4 adalah sinyal seed yang sudah terhubung ke case-002.
        missing_reason = await client.post("/api/v1/signals/4/unlink", json={"reason": "  "})
        assert missing_reason.status_code == 422


@pytest.mark.asyncio
async def test_mbg001_and_seed_still_intact():
    """Regressi: golden path MBG-001 & sinyal seed tetap konsisten."""
    async with await make_client() as client:
        c = (await client.get("/api/v1/cases/case-001")).json()
        assert c["case_number"] == "MBG-001"
        assert c["evidence"], "MBG-001 harus tetap punya bukti"
        signals = (await client.get("/api/v1/signals")).json()["items"]
        cases = {x["case_id"] for x in (await client.get("/api/v1/cases")).json()["items"]}
        for s in signals:
            assert s["case_id"] is None or s["case_id"] in cases


@pytest.mark.asyncio
async def test_case_ownership_edit_roundtrip():
    """Kepemilikan dapat diubah, dikosongkan, dan terbaca ulang apa adanya."""
    async with await make_client() as client:
        cases = (await client.get("/api/v1/cases")).json()["items"]
        cid = cases[0]["case_id"]
        before_status = cases[0]["status"]

        set_res = await client.patch(f"/api/v1/cases/{cid}", json={
            "primary_owner": "Rina Prasetyo",
            "handling_team": "Unit Audit Distrik",
            "secondary_owner": "Bagas Nugroho",
            # Status dikirim ulang tanpa berubah: tidak boleh jadi event audit.
            "status": before_status,
        })
        assert set_res.status_code == 200
        assert not any(e["event_type"] == "case_status_changed" for e in set_res.json()["audit_events"])

        detail = (await client.get(f"/api/v1/cases/{cid}")).json()
        assert detail["primary_owner"] == "Rina Prasetyo"
        assert detail["handling_team"] == "Unit Audit Distrik"
        assert detail["secondary_owner"] == "Bagas Nugroho"
        # Alias lama ikut tersinkron.
        assert detail["assigned_investigator"] == "Rina Prasetyo"
        assert detail["assigned_unit"] == "Unit Audit Distrik"

        # String kosong = dilepas eksplisit, bukan diabaikan dan bukan fallback
        # diam-diam ke assigned_investigator lama.
        await client.patch(f"/api/v1/cases/{cid}", json={"primary_owner": "", "secondary_owner": ""})
        cleared = (await client.get(f"/api/v1/cases/{cid}")).json()
        assert cleared["primary_owner"] is None
        assert cleared["secondary_owner"] is None
        assert cleared["handling_team"] == "Unit Audit Distrik"


@pytest.mark.asyncio
async def test_case_detail_lists_every_child_ticket():
    """Ringkasan kasus harus punya semua tiket anak, bukan hanya yang pertama."""
    async with await make_client() as client:
        cases = (await client.get("/api/v1/cases")).json()["items"]
        cid = cases[0]["case_id"]
        for title in ("Workstream verifikasi", "Workstream klarifikasi vendor"):
            assert (await client.post(f"/api/v1/cases/{cid}/tickets", json={"title": title})).status_code == 200

        detail = (await client.get(f"/api/v1/cases/{cid}")).json()
        ids = [t["id"] for t in detail["tickets"]]
        assert len(ids) >= 2
        # `ticket_id` hanya alias tiket pertama — chip UI tidak boleh memakainya.
        assert detail["ticket_id"] == ids[0]
        assert detail["ticket_summary"]["total"] == len(ids)
