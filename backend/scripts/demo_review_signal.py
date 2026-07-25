"""Demo skrip: tinjau signal yang belum terhubung ke kasus.

Menunjukkan alur "Tinjau & Bentuk Kasus" end-to-end lewat store runtime:
daftar sinyal belum dibentuk kasus -> cari terkait -> penilaian awal ->
bentuk kasus baru -> verifikasi kasus & audit.

    cd backend && python -m scripts.demo_review_signal
"""

from __future__ import annotations

from app import demo_data as d
from app import review_store as rs


def main() -> None:
    unlinked = [s for s in d.SIGNALS if not s.get("case_id")]
    print("=== Sinyal belum dibentuk kasus ===")
    for s in unlinked:
        print(f"  #{s['id']} [{s['source']}] {s['summary'][:60]} (keyakinan {int(s['source_confidence']*100)}%)")

    target = unlinked[0]["id"]
    print(f"\n=== Tinjau sinyal #{target} ===")

    rel = rs.find_related(target)
    print(f"Terkait: {len(rel['case_candidates'])} kasus, "
          f"{len(rel['signal_candidates'])} sinyal, {len(rel['evidence_candidates'])} bukti "
          f"(sumber: {rel['source_note']})")

    a = rs.initial_assessment(target)
    print(f"Penilaian awal: {a['priority_label']} (skor {a['final_priority_score']}, keyakinan {a['confidence_score']}%)")

    res = rs.review_signal(target, {
        "decision": "create",
        "searched_related": True,
        "new_case": {"title": "Demo: tinjauan sinyal warganet", "issue_category": "porsi protein kurang"},
        "assignment": {"investigator": "Operator Dewi", "urgency": "Sedang", "sla": "48h",
                       "recommended_action": "Minta klarifikasi awal untuk mengidentifikasi vendor dan lokasi."},
        "override": {"operator_adjusted": True, "priority_label": "Tinggi",
                     "final_priority_score": 70, "override_reason": "beberapa sinyal serupa di wilayah sama"},
    })
    print(f"\nHasil: {res['outcome']} -> {res['case_number']} (redirect {res['redirect']})")

    case = d.case_detail(res["case_id"])
    print(f"Kasus terbuka: {case['title']}")
    print(f"Sinyal tertaut: {rs.get_signal(target)['case_id']} / {rs.get_signal(target)['status']}")
    print("Audit kasus:")
    for e in case["audit_events"]:
        print(f"  - {e['event_type']}: {e['description'][:70]}")


def scenario_belatung() -> None:
    """Skenario evidence fusion: laporan resmi (4.jpg) + sinyal media sosial (26.jpg)."""
    print("\n\n########## Skenario: kontaminasi belatung (Lampung) ##########")
    print("Laporan resmi #19 (4.jpg) & sinyal media sosial #20 (26.jpg) — keduanya belum dibentuk kasus.")

    # Bentuk kasus dari laporan resmi #19.
    created = rs.review_signal(19, {
        "decision": "create", "searched_related": True,
        "new_case": {"title": "Dugaan kontaminasi makanan pada SDN 1 Karang Agung",
                     "issue_category": "dugaan keamanan pangan", "school": "SDN 1 Karang Agung"},
        "assignment": {"investigator": "Operator Dewi", "urgency": "Kritis", "sla": "24h",
                       "recommended_action": "Jadwalkan verifikasi lapangan segera, amankan informasi pendukung, dan minta klarifikasi penyedia makanan."},
        "override": {"operator_adjusted": True, "priority_label": "Kritis",
                     "final_priority_score": 82, "override_reason": "kanal resmi + lokasi spesifik + lampiran"},
    })
    cid = created["case_id"]
    print(f"Kasus dibentuk: {created['case_number']} ({cid}) — bukti utama 4.jpg, tanpa tiket otomatis.")

    # Cari terkait dari laporan resmi -> sinyal media sosial #20 muncul (skor sedang).
    rel = rs.find_related(19)
    social = next(c for c in rel["signal_candidates"] if c["id"] == 20)
    print(f"Kandidat pendukung #20: skor {social['match_score']} — {social['label']}")
    for r in social["reasons"]:
        print(f"    · {r}")

    # Operator menyetujui penggabungan sinyal media sosial #20.
    merged = rs.review_signal(20, {
        "decision": "merge", "searched_related": True, "target_case_id": cid,
        "selected_signal_ids": [20],
        "assignment": {"investigator": "Operator Dewi"},
        "override": {"operator_adjusted": True, "priority_label": "Kritis",
                     "final_priority_score": 85, "override_reason": "tambahan sinyal wilayah sama"},
    })
    case = d.case_detail(cid)
    print(f"Merge diterima operator: {[e['event_type'] for e in merged['audit_events']]}")
    print("Bukti kasus:")
    for e in case["evidence"]:
        print(f"    - {e['file_path']} | {e['source']} | {e['review_status']}")

    # Operator melepaskan kembali sinyal media sosial #20 dari kasus (re-triase).
    print("\n--- Lepaskan sinyal #20 dari kasus (dengan alasan) ---")
    unlink = rs.unlink_signal(20, {"reason": "lokasi/waktu belum terkonfirmasi; perlu klarifikasi awal"})
    print(f"Audit pelepasan: {[e['event_type'] for e in unlink['audit_events']]}")
    sig20 = rs.get_signal(20)
    print(f"Signal #20 kembali: case_id={sig20['case_id']} status={sig20['status']}")
    case2 = d.case_detail(cid)
    print("Bukti kasus setelah pelepasan (26.jpg dilepas, 4.jpg tetap):")
    for e in case2["evidence"]:
        print(f"    - {e['file_path']} | {e['source']}")
    still = any(e["file_path"].endswith("/26.jpg") for e in d.EVIDENCE)
    print(f"Baris/aset 26.jpg tetap ada (tidak dihapus): {still}")


if __name__ == "__main__":
    main()
    scenario_belatung()
