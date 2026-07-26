"""Runtime store untuk workflow "Tinjau & Bentuk Kasus".

Menyimpan perubahan yang dibuat operator (gabung/kasus baru/tunda) sebagai
STATE RUNTIME di atas data seed — tidak mengubah seed asli secara destruktif.
Karena ``demo_data`` menurunkan respons dari list/dict modul ``seed_data`` yang
mutable, menambah kasus/risiko dan menautkan sinyal ke list yang sama membuat
perubahan langsung terlihat di Kotak Masuk Sinyal, Detail Kasus, dan Jejak Audit
selama proses berjalan (satu sesi).

Bila PostgreSQL aktif, perubahan yang sama juga ditulis ke DB lewat
``app.persistence`` (best-effort, tidak menggagalkan aksi bila DB tidak
tersedia — mode demo tetap konsisten).
"""

from __future__ import annotations

from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any

from fastapi import HTTPException, status

from app import persistence, seed_data as sd, ticketing
from app.runtime_store import all_signals, get_signal as get_runtime_signal
from app.services.scoring.risk_scorer import score_signal

# Peta prioritas -> skor awal (selaras dengan _build_risk di seed_data).
PRIORITY_SCORE = {"Kritis": 88, "Tinggi": 78, "Sedang": 58, "Rendah": 38}
# SLA usulan pada layar review. Diturunkan dari SLA_POLICIES agar tidak
# menjadi tabel ketiga yang berbeda dari mesin SLA tiket.
URGENCY_TO_SLA = {
    label: ticketing.sla_label(ticketing.policy_for(label))
    for label in ("Kritis", "Tinggi", "Sedang", "Rendah")
}

MANUAL_VENDOR_ID = "__manual__"
UNKNOWN_LOCATION = "Belum teridentifikasi"
INVESTIGATORS = [item["name"] for item in sd.INVESTIGATOR_REGISTRY]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_signal(signal_id: int) -> dict[str, Any]:
    sig = get_runtime_signal(signal_id)
    if sig:
        return sig
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sinyal '{signal_id}' tidak ditemukan")


def _known(value: str | None) -> str:
    value = (value or "").strip()
    return "" if not value or value == UNKNOWN_LOCATION else value


def _assignment_matches(item: dict[str, Any], region: str, district: str) -> bool:
    if not region:
        return bool(item.get("national"))
    if item.get("national"):
        return True
    if region not in item.get("provinces", []):
        return False
    districts = item.get("districts", [])
    return not district or not districts or district in districts


def _location_vendor_ids(region: str, district: str, school: str) -> set[str]:
    if not region:
        return set()
    ids: set[str] = set()
    for province in sd.LOCATION_REGISTRY:
        if province["province"] != region:
            continue
        district_items = []
        for item in province["districts"]:
            if district and item["name"] != district:
                continue
            district_items.append(item)
        if school:
            school_items = [item for item in district_items if school in item["schools"]]
            # Sekolah manual yang belum masuk registry tetap memakai kandidat
            # pada kabupaten/kota terpilih, bukan mengosongkan daftar secara
            # keliru.
            district_items = school_items or district_items
        for item in district_items:
            ids.update(item["vendor_ids"])
    return ids


def assignment_options(region: str | None = None, district: str | None = None,
                       school: str | None = None) -> dict[str, Any]:
    """Kandidat vendor/penugasan terfilter dari registry kanonik."""
    region = _known(region)
    district = _known(district)
    school = _known(school)
    vendor_ids = _location_vendor_ids(region, district, school)
    vendors = [sd.VENDOR_BY_ID[v_id] for v_id in vendor_ids if v_id in sd.VENDOR_BY_ID]
    vendors.sort(key=lambda item: item["name"])
    investigators = [item for item in sd.INVESTIGATOR_REGISTRY if _assignment_matches(item, region, district)]
    units = [item for item in sd.UNIT_REGISTRY if _assignment_matches(item, region, district)]
    message = None
    if not region:
        message = "Lengkapi wilayah atau sekolah untuk menampilkan kandidat penyedia yang relevan."
    elif not vendors:
        message = "Belum ada kandidat penyedia pada registry wilayah ini."
    return {
        "locations": sd.LOCATION_REGISTRY,
        "vendors": vendors,
        "investigators": investigators,
        "units": units,
        "vendor_message": message,
        "manual_vendor": {"id": MANUAL_VENDOR_ID, "label": "Penyedia belum terdaftar / masukkan dari laporan"},
        "governance_notice": sd.ASSIGNMENT_GOVERNANCE_NOTICE,
    }


def _validate_assignment(region: str, district: str, school: str, assignment: dict[str, Any]) -> None:
    options = assignment_options(region, district, school)
    investigator_names = {item["name"] for item in options["investigators"]}
    unit_names = {item["name"] for item in options["units"]}
    if assignment.get("investigator") and assignment["investigator"] not in investigator_names:
        raise HTTPException(status_code=422, detail="Investigator tidak sesuai dengan cakupan wilayah kasus.")
    if assignment.get("unit") and assignment["unit"] not in unit_names:
        raise HTTPException(status_code=422, detail="Unit penanggung jawab tidak sesuai dengan cakupan wilayah kasus.")


def _add_audit(case_id: str | None, event_type: str, description: str,
               actor: str = "Operator Demo", role: str = "Operator Distrik",
               ticket_id: str | None = None) -> dict[str, Any]:
    event = {
        "id": (max((a["id"] for a in sd.AUDIT), default=0) + 1),
        "case_id": case_id,
        "ticket_id": ticket_id,
        "event_type": event_type,
        "actor": actor,
        "role": role,
        "description": description,
        "timestamp": _now(),
    }
    sd.AUDIT.insert(0, event)
    persistence.persist("audit", event)
    return event


# ── Pencarian terkait (deterministik, sumber data internal) ──────────────
def _sim(a: str, b: str) -> float:
    return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()


_STOP = {"di", "dan", "yang", "pada", "sebuah", "porsi", "kasus", "sinyal", "laporan",
         "ada", "anak", "dugaan", "makanan", "menyebut", "unggahan", "lokasi", "belum",
         "pengawas", "media", "sosial"}


def _words(text: str) -> set[str]:
    return {w.strip(".,;:").lower() for w in (text or "").split() if len(w) > 2 and w.lower() not in _STOP}


def _keyword_overlap(a: str, b: str) -> bool:
    return len(_words(a) & _words(b)) >= 1


def _shared_keywords(a: str, b: str) -> set[str]:
    """Kata kunci isu spesifik yang muncul di kedua teks (mis. belatung, mbg)."""
    return _words(a) & _words(b)


def _hours_between(a: str, b: str) -> float:
    return abs(datetime.fromisoformat(a) - datetime.fromisoformat(b)).total_seconds() / 3600


def find_related(signal_id: int) -> dict[str, Any]:
    """Pencocokan deterministik terhadap kasus, sinyal, dan bukti internal.

    Tanpa scraping/real-time, tanpa model eksternal. Skor & alasan bersifat
    aturan sederhana untuk membantu operator, bukan pencocokan final.
    """
    signal = get_signal(signal_id)
    sig_issue = signal.get("issue_category") or ""
    sig_region = signal.get("region") or ""
    sig_school = signal.get("school") or ""
    sig_vendor = signal.get("vendor_id")
    sig_summary = signal.get("summary") or ""
    sig_time = signal.get("created_at") or ""

    # Kandidat kasus yang sudah ada.
    case_candidates = []
    for case in sd.CASES:
        vendor = sd.VENDOR_BY_ID.get(case["vendor_id"], {})
        score = 0
        reasons: list[str] = []
        if sig_vendor and sig_vendor == case["vendor_id"]:
            score += 45
            reasons.append("Vendor yang sama")
        if sig_issue and sig_issue == case["issue_category"]:
            score += 25
            reasons.append("Kategori isu sama")
        if sig_region and sig_region == vendor.get("region"):
            score += 15
            reasons.append("Wilayah serupa")
        if sig_school and sig_school == case["school"]:
            score += 15
            reasons.append("Sekolah serupa")
        if _keyword_overlap(sig_summary, case["title"]):
            score += 15
            reasons.append("Kata kunci isu serupa")
        if sig_time and case.get("created_at") and abs(
            (datetime.fromisoformat(sig_time) - datetime.fromisoformat(case["created_at"])).days
        ) <= 3:
            score += 10
            reasons.append("Waktu laporan berdekatan")
        # Untuk sinyal minim data, tetap tawarkan kecocokan lemah berbasis teks.
        if score == 0 and _sim(sig_summary, case["title"]) >= 0.3:
            score += 8
            reasons.append("Kemiripan teks ringkasan")
        if score > 0:
            case_candidates.append({
                "case_id": case["case_id"],
                "case_number": sd.case_number(case["case_id"]),
                "title": case["title"],
                "vendor_name": vendor.get("name", "Belum teridentifikasi"),
                "region": vendor.get("region", "-"),
                "school": case["school"],
                "issue_category": case["issue_category"],
                "priority_label": case["priority_label"],
                "created_at": case["created_at"],
                "match_score": min(score, 95),
                "reasons": reasons,
            })
    case_candidates.sort(key=lambda c: c["match_score"], reverse=True)

    # Sinyal lain yang belum terhubung.
    sig_text = signal.get("text") or ""
    sig_district = signal.get("district") or ""
    signal_candidates = []
    for other in all_signals():
        if other["id"] == signal_id or other.get("case_id"):
            continue
        score = 0
        reasons: list[str] = []
        # Kata kunci isu spesifik (mis. belatung, mbg) memberi sinyal terkuat.
        shared_kw = _shared_keywords(f"{sig_summary} {sig_text}", f"{other.get('summary','')} {other.get('text','')}")
        if shared_kw:
            score += 30
            reasons.append(f"Kata kunci isu serupa: {', '.join(sorted(shared_kw)[:3])}")
        elif _keyword_overlap(sig_summary, other.get("summary", "")):
            score += 20
            reasons.append("Kata kunci isu serupa")
        if sig_region and sig_region == other.get("region"):
            score += 20
            reasons.append(f"Wilayah provinsi sama: {sig_region}")
        if other.get("created_at") and sig_time and _hours_between(sig_time, other["created_at"]) <= 48:
            score += 10
            reasons.append("Waktu publikasi berdekatan")
        # Catatan pra-verifikasi: lokasi spesifik post belum tentu cocok.
        other_district = other.get("district") or ""
        if sig_district and (not other_district or other_district == "Belum teridentifikasi"):
            reasons.append("Lokasi sekolah/kabupaten pada sinyal ini belum terkonfirmasi")
        if score > 0:
            signal_candidates.append({
                "id": other["id"],
                "summary": other["summary"],
                "source": other["source"],
                "region": other.get("region", "-"),
                "created_at": other["created_at"],
                # Skor sengaja dijaga di tingkat sedang (cap 60), bukan sangat tinggi.
                "match_score": min(score, 60),
                "reasons": reasons,
                "attachment_path": other.get("attachment_path"),
                "attachment_title": other.get("attachment_title"),
                "label": "Kandidat sinyal pendukung — perlu peninjauan operator",
            })
    signal_candidates.sort(key=lambda s: s["match_score"], reverse=True)

    # Bukti yang mungkin relevan (dari kasus dengan kategori isu sama).
    evidence_candidates = []
    for ev in sd.EVIDENCE:
        case = sd.CASE_BY_ID.get(ev["case_id"], {})
        score = 0
        reasons = []
        if sig_issue and sig_issue == case.get("issue_category"):
            score += 30
            reasons.append("Kategori isu sama")
        if _keyword_overlap(sig_summary, ev.get("title", "")):
            score += 15
            reasons.append("Kata kunci isu serupa")
        if score > 0:
            evidence_candidates.append({
                "id": ev["id"],
                "title": ev["title"],
                "type": ev["type"],
                "file_path": ev.get("file_path"),
                "case_id": ev["case_id"],
                "confidence_score": ev["confidence_score"],
                "match_score": min(score, 90),
                "reasons": reasons,
            })
    evidence_candidates.sort(key=lambda e: e["match_score"], reverse=True)

    return {
        "signal_id": signal_id,
        "source_note": "Hasil dari sumber data demo/internal, bukan crawling real-time.",
        "case_candidates": case_candidates[:5],
        "signal_candidates": signal_candidates[:5],
        "evidence_candidates": evidence_candidates[:6],
        "ai_notice": sd.GOVERNANCE_NOTICE,
    }


# ── System pre-assessment (pra-verifikasi) untuk sinyal ──────────────────
def initial_assessment(signal_id: int) -> dict[str, Any]:
    return score_signal(get_signal(signal_id))


# ── Aksi review: merge / create / defer ──────────────────────────────────
def _next_case_id() -> str:
    nums = [int("".join(ch for ch in c["case_id"] if ch.isdigit()) or 0) for c in sd.CASES]
    return f"case-{(max(nums, default=0) + 1):03d}"


def _score_value(data: dict[str, Any], key: str, default: int) -> int:
    """Ambil skor numerik; nilai ``None`` diperlakukan sebagai tidak ada (bukan 0)."""
    val = data.get(key)
    return default if val is None else int(val)


def _merge_assessment(signal_id: int, override: dict[str, Any]) -> dict[str, Any]:
    """Gabungkan penilaian awal dengan override operator tanpa menimpa dengan null."""
    base = initial_assessment(signal_id)
    clean = {k: v for k, v in override.items() if v is not None}
    return {**base, **clean}


def _register_risk(case_id: str, vendor: dict, override: dict[str, Any], *, region: str | None = None,
                   vendor_name: str | None = None) -> dict[str, Any]:
    risk = {
        "id": (max((r["id"] for r in sd.RISK), default=0) + 1),
        "case_id": case_id,
        "vendor_id": vendor["id"],
        "vendor_name": vendor_name or vendor["name"],
        "region": region or vendor["region"],
        "severity_score": _score_value(
            override, "severity_score", _score_value(override, "final_priority_score", 45),
        ),
        "confidence_score": _score_value(override, "confidence_score", 45),
        "actionability_score": _score_value(override, "actionability_score", 30),
        "nutrition_score": override.get("nutrition_score"),
        "final_priority_score": override["final_priority_score"],
        "priority_label": override["priority_label"],
        "explanation": override.get("explanation", "Penilaian ditetapkan saat pembentukan kasus."),
        "recommended_action": override.get("recommended_action", "Kumpulkan bukti tambahan."),
        "computed_at": _now(),
        "ai_notice": sd.GOVERNANCE_NOTICE,
    }
    sd.RISK.append(risk)
    sd.RISK_BY_CASE[case_id] = risk
    persistence.persist("risk", risk)
    return risk


def _case_has_evidence(case_id: str, *, signal_id: int | None = None,
                       file_path: str | None = None) -> bool:
    """True bila kasus sudah punya bukti aktif dari sinyal/berkas yang sama."""
    for e in sd.EVIDENCE:
        if e["case_id"] != case_id or e.get("unlinked_from_case"):
            continue
        if signal_id is not None and e.get("signal_id") == signal_id:
            return True
        if file_path and e.get("file_path") == file_path:
            return True
    return False


def _add_evidence_from_signal(case_id: str, signal: dict[str, Any]) -> dict[str, Any] | None:
    """Materialkan lampiran sinyal menjadi bukti kasus (bila ada lampiran).

    Bukti berstatus pra-verifikasi ("Perlu Ditinjau"); bukan bukti final.
    Idempoten: bila bukti untuk sinyal/berkas ini sudah ada pada kasus,
    tidak dibuat duplikat (return None).
    """
    path = signal.get("attachment_path")
    if not path:
        return None
    if _case_has_evidence(case_id, signal_id=signal["id"], file_path=path):
        return None
    ev = {
        "id": (max((e["id"] for e in sd.EVIDENCE), default=0) + 1),
        "case_id": case_id,
        "signal_id": signal["id"],
        "type": "photo",
        "title": signal.get("attachment_title") or "Lampiran sinyal",
        "file_path": path,
        "linked_entity": sd.case_number(case_id),
        "source": signal.get("attachment_source") or signal.get("source") or "Sinyal",
        "ocr_result": None,
        "image_text_match_score": None,
        "duplicate_score": None,
        "confidence_score": round(signal.get("source_confidence", 0.5), 2),
        "review_status": "Perlu Ditinjau",
        "reviewer_note": signal.get("attachment_note")
        or "Lampiran sinyal sebagai bukti pra-verifikasi; perlu ditinjau operator.",
        "created_at": _now(),
    }
    sd.EVIDENCE.append(ev)
    persistence.persist("evidence", ev)
    return ev


# ── Kandidat terkait yang dicentang operator (fusion) ────────────────────
def _validate_selected_items(origin_signal_id: int, signal_ids: list[int],
                             evidence_ids: list[int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validasi kandidat terpilih SEBELUM mutasi apa pun (fail-fast).

    - ID yang tidak dikenal -> 422; tidak ada status partial pada kandidat.
    - Sinyal asal dan sinyal yang sudah terhubung dilewati (idempoten):
      tidak ada relasi ganda maupun evidence ganda.
    """
    extra_signals: list[dict[str, Any]] = []
    for sid in signal_ids:
        if sid == origin_signal_id:
            continue
        match = next((s for s in all_signals() if s["id"] == sid), None)
        if match is None:
            raise HTTPException(status_code=422, detail=f"Sinyal terpilih '{sid}' tidak ditemukan.")
        if match.get("case_id"):
            continue
        if any(s["id"] == sid for s in extra_signals):
            continue
        extra_signals.append(match)
    extra_evidence: list[dict[str, Any]] = []
    for eid in evidence_ids:
        match = next((e for e in sd.EVIDENCE if e["id"] == eid), None)
        if match is None:
            raise HTTPException(status_code=422, detail=f"Bukti terpilih '{eid}' tidak ditemukan.")
        if any(e["id"] == eid for e in extra_evidence):
            continue
        extra_evidence.append(match)
    return extra_signals, extra_evidence


def _link_selected_items(case: dict[str, Any], extra_signals: list[dict[str, Any]],
                         extra_evidence: list[dict[str, Any]], audit: list[dict[str, Any]],
                         actor: str) -> tuple[list[int], list[int]]:
    """Tautkan sinyal & bukti yang dicentang operator ke kasus (create maupun merge).

    Setiap sinyal ditautkan (status "Terhubung ke Kasus"), lampirannya
    dimaterialkan sebagai bukti kasus tanpa duplikasi, dan setiap aksi dicatat
    sebagai keputusan operator pada jejak audit. Bukti terpilih dari kasus lain
    disalin sebagai baris bukti baru pada kasus ini; baris asal tidak diubah.
    """
    cid = case["case_id"]
    linked_signal_ids: list[int] = []
    added_evidence_ids: list[int] = []

    def track_ticket(ev_id: int) -> None:
        ticket = sd.TICKET_BY_CASE.get(cid)
        if ticket and ev_id not in ticket["linked_evidence_ids"]:
            ticket["linked_evidence_ids"].append(ev_id)
            persistence.persist("ticket", ticket)

    for sig in extra_signals:
        sig["case_id"] = cid
        sig["status"] = "Terhubung ke Kasus"
        sig["issue_category"] = case["issue_category"]
        persistence.persist("signal", sig)
        linked_signal_ids.append(sig["id"])
        if "sosial" in (sig.get("source") or "").lower():
            audit.append(_add_audit(
                cid, "social_signal_reviewed",
                f"Sinyal media sosial #{sig['id']} ditinjau operator sebagai sinyal pendukung, "
                f"bukan bukti final atau konfirmasi kejadian.", actor=actor))
        audit.append(_add_audit(
            cid, "signal_merged",
            f"Operator {actor} menautkan sinyal #{sig['id']} ke {sd.case_number(cid)} sebagai sinyal pendukung. "
            f"Keterkaitan lokasi/waktu belum dikonfirmasi dan tetap memerlukan verifikasi.",
            actor=actor))
        ev = _add_evidence_from_signal(cid, sig)
        if ev:
            added_evidence_ids.append(ev["id"])
            track_ticket(ev["id"])
            audit.append(_add_audit(
                cid, "evidence_added",
                f"Bukti '{ev['title']}' (sumber {ev['source']}) ditambahkan dari sinyal #{sig['id']}. "
                f"Status: Perlu Ditinjau.", actor=actor))

    for src in extra_evidence:
        if src["case_id"] == cid and not src.get("unlinked_from_case"):
            continue  # sudah menjadi bukti aktif kasus ini
        if _case_has_evidence(cid, file_path=src.get("file_path")):
            continue  # berkas yang sama sudah ada pada kasus; jangan gandakan
        ev = {
            "id": (max((e["id"] for e in sd.EVIDENCE), default=0) + 1),
            "case_id": cid,
            "signal_id": None,
            "type": src["type"],
            "title": src["title"],
            "file_path": src.get("file_path"),
            "linked_entity": sd.case_number(cid),
            "source": src.get("source") or "Bukti terkait",
            "ocr_result": src.get("ocr_result"),
            "image_text_match_score": src.get("image_text_match_score"),
            "duplicate_score": src.get("duplicate_score"),
            "confidence_score": src.get("confidence_score", 0.5),
            "review_status": "Perlu Ditinjau",
            "reviewer_note": (f"Bukti ditautkan operator dari {sd.case_number(src['case_id'])}; "
                              f"tetap memerlukan peninjauan pada kasus ini."),
            "created_at": _now(),
        }
        sd.EVIDENCE.append(ev)
        persistence.persist("evidence", ev)
        added_evidence_ids.append(ev["id"])
        track_ticket(ev["id"])
        audit.append(_add_audit(
            cid, "evidence_added",
            f"Bukti '{ev['title']}' ditautkan operator dari {sd.case_number(src['case_id'])}. "
            f"Status: Perlu Ditinjau.", actor=actor))

    if linked_signal_ids or added_evidence_ids:
        case["updated_at"] = _now()
        persistence.persist("case", case)
    return linked_signal_ids, added_evidence_ids


def _case_snapshot(case_id: str) -> dict[str, Any]:
    """Kembalikan snapshot kasus dari store yang sama dengan GET /cases."""
    # Import lokal menghindari circular import saat modul API memuat kedua store.
    from app import demo_data

    # COMPLAINTS/REPORTS/DAILY_REPORTS adalah proyeksi atas kasus & sinyal;
    # kasus/tautan baru harus tercermin sebelum snapshot dibaca.
    demo_data.rebuild_derived()
    return demo_data.case_detail(case_id)


def _effective_location(signal: dict[str, Any], new_case: dict[str, Any]) -> tuple[str, str, str]:
    def value(key: str, fallback: str | None) -> str:
        if key in new_case and new_case.get(key) is not None:
            return _known(new_case.get(key)) or UNKNOWN_LOCATION
        return _known(fallback) or UNKNOWN_LOCATION

    region = value("region", signal.get("region"))
    district = value("district", signal.get("district"))
    school = value("school", signal.get("school"))
    return region, district, school


def review_signal(signal_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    signal = get_signal(signal_id)
    if signal.get("case_id"):
        raise HTTPException(status_code=409, detail="Sinyal sudah terhubung ke kasus.")

    decision = payload["decision"]
    is_social = "sosial" in (signal.get("source") or "").lower()
    # Assignee bukan aktor perubahan; jejak audit harus mencatat operator
    # yang mengonfirmasi penugasan.
    actor = "Operator Demo"

    audit: list[dict[str, Any]] = []
    # Sinyal media sosial mendapat event khusus; keterkaitan diterima OPERATOR.
    audit.append(_add_audit(
        None,
        "social_signal_reviewed" if is_social else "signal_reviewed",
        f"Sinyal #{signal_id} ditinjau operator." + (
            " Sinyal media sosial diperiksa sebagai sinyal pendukung, bukan bukti final." if is_social else ""
        ),
        actor=actor,
    ))
    if payload.get("searched_related"):
        audit.append(_add_audit(None, "related_items_searched",
                                "Operator mencari sinyal, laporan, dan bukti terkait.", actor=actor))

    assignment = payload.get("assignment") or {}
    override = payload.get("override") or {}

    if decision == "merge":
        target = payload.get("target_case_id")
        case = sd.CASE_BY_ID.get(target)
        if not case:
            raise HTTPException(status_code=404, detail=f"Kasus target '{target}' tidak ditemukan.")
        target_vendor = sd.VENDOR_BY_ID.get(case["vendor_id"], sd.VENDOR_BY_ID["vnd-unknown"])
        target_region = case.get("region") or target_vendor.get("region")
        target_district = case.get("district") or target_vendor.get("district")
        target_school = case.get("school") or ""
        _validate_assignment(target_region, target_district, target_school, assignment)
        # Kandidat yang dicentang operator ikut diproses (fail-fast sebelum mutasi).
        extra_signals, extra_evidence = _validate_selected_items(
            signal_id, payload.get("selected_signal_ids") or [], payload.get("selected_evidence_ids") or [])
        signal["case_id"] = target
        signal["status"] = "Terhubung ke Kasus"
        signal["issue_category"] = case["issue_category"]
        persistence.persist("signal", signal)
        case["updated_at"] = _now()
        persistence.persist("case", case)
        # signal_merged: penggabungan DILAKUKAN/DITERIMA operator (bukan otomatis).
        audit.append(_add_audit(
            target, "signal_merged",
            f"Operator {actor} menggabungkan sinyal #{signal_id} ke {sd.case_number(target)} sebagai sinyal pendukung. "
            f"Keterkaitan lokasi/waktu belum dikonfirmasi dan tetap memerlukan verifikasi.",
            actor=actor,
        ))
        # Lampiran sinyal menjadi bukti kasus.
        ev = _add_evidence_from_signal(target, signal)
        if ev:
            ticket = sd.TICKET_BY_CASE.get(target)
            if ticket and ev["id"] not in ticket["linked_evidence_ids"]:
                ticket["linked_evidence_ids"].append(ev["id"])
                persistence.persist("ticket", ticket)
            audit.append(_add_audit(target, "evidence_added",
                                    f"Bukti '{ev['title']}' (sumber {ev['source']}) ditambahkan dari sinyal #{signal_id}. "
                                    f"Status: Perlu Ditinjau.", actor=actor))
        # risk_reassessed hanya bila operator memberi rekomendasi skor baru.
        if override.get("operator_adjusted") and override.get("final_priority_score") is not None:
            risk = sd.RISK_BY_CASE.get(target)
            if risk:
                risk["final_priority_score"] = override["final_priority_score"]
                risk["priority_label"] = override.get("priority_label", risk["priority_label"])
                persistence.persist("risk", risk)
            audit.append(_add_audit(
                target, "risk_reassessed",
                f"Rekomendasi pra-verifikasi: skor diperbarui menjadi {override['final_priority_score']} "
                f"({override.get('priority_label', '-')}) setelah tambahan sinyal. Operator dapat override. "
                f"Alasan: {override.get('override_reason', '-')}.",
                actor=actor,
            ))
        if assignment.get("investigator"):
            before = case.get("assigned_investigator") or "Belum ditetapkan"
            case["assigned_investigator"] = assignment["investigator"]
            persistence.persist("case", case)
            audit.append(_add_audit(target, "investigator_assigned",
                                    f"Investigator ditetapkan. Sebelum: {before}; sesudah: {assignment['investigator']}.",
                                    actor=actor))
        if assignment.get("unit"):
            before = case.get("assigned_unit") or "Belum ditetapkan"
            case["assigned_unit"] = assignment["unit"]
            persistence.persist("case", case)
            audit.append(_add_audit(target, "responsible_unit_assigned",
                                    f"Unit penanggung jawab ditetapkan. Sebelum: {before}; sesudah: {assignment['unit']}.",
                                    actor=actor))
        # Sinyal/bukti terkait yang dicentang ikut ditautkan ke kasus target.
        extra_linked, extra_evidence_ids = _link_selected_items(case, extra_signals, extra_evidence, audit, actor)
        from app.services.copilot.service import index_case_for_copilot
        index_case_for_copilot(target)
        return {"outcome": "merged", "case_id": target, "case_number": sd.case_number(target),
                "redirect": f"/cases/{target}", "audit_events": audit,
                "linked_signal_ids": [signal_id, *extra_linked],
                "added_evidence_ids": ([ev["id"]] if ev else []) + extra_evidence_ids,
                # Frontend dapat menyinkronkan state tanpa menunggu/race dengan
                # navigasi ke halaman detail kasus.
                "case": _case_snapshot(target), "ai_notice": sd.GOVERNANCE_NOTICE}

    if decision == "create":
        new_case_data = payload.get("new_case") or {}
        region, district, school = _effective_location(signal, new_case_data)
        _validate_assignment(region, district, school, assignment)
        requested_vendor_id = new_case_data.get("vendor_id") or signal.get("vendor_id") or "vnd-unknown"
        if requested_vendor_id not in {"vnd-unknown", MANUAL_VENDOR_ID}:
            candidate_ids = _location_vendor_ids(region, district, school)
            if requested_vendor_id not in candidate_ids:
                raise HTTPException(status_code=422, detail="Vendor tidak sesuai dengan cakupan wilayah kasus.")
        manual_vendor_name = (new_case_data.get("vendor_name") or "").strip()
        if requested_vendor_id == MANUAL_VENDOR_ID and not manual_vendor_name:
            raise HTTPException(status_code=422, detail="Nama penyedia wajib diisi untuk opsi penyedia manual.")
        # Kandidat yang dicentang operator ikut diproses (fail-fast sebelum mutasi).
        extra_signals, extra_evidence = _validate_selected_items(
            signal_id, payload.get("selected_signal_ids") or [], payload.get("selected_evidence_ids") or [])
        vendor_id = "vnd-unknown" if requested_vendor_id == MANUAL_VENDOR_ID else requested_vendor_id
        vendor = sd.VENDOR_BY_ID.get(vendor_id, sd.VENDOR_BY_ID["vnd-unknown"])
        cid = _next_case_id()
        case = {
            "case_id": cid,
            "vendor_id": vendor["id"],
            "vendor_name_override": manual_vendor_name or None,
            "vendor_source_note": (new_case_data.get("vendor_source_note") or "").strip() or None,
            "region": region,
            "district": district,
            "school": school,
            "issue_category": new_case_data.get("issue_category") or signal.get("issue_category") or "belum diklasifikasi",
            "priority_label": override.get("priority_label", "Sedang"),
            "severity": override.get("priority_label", "Sedang"),
            # A case starts as an actively monitored aggregate; it can be
            # handled directly without a child ticket.
            "status": "Open & Monitored",
            "title": new_case_data.get("title") or f"Tinjauan sinyal: {signal['summary'][:80]}",
            "assigned_investigator": assignment.get("investigator") or None,
            "assigned_unit": assignment.get("unit") or None,
            "primary_owner": assignment.get("investigator") or None,
            "handling_team": assignment.get("unit") or None,
            "secondary_owner": assignment.get("secondary_owner") or None,
            "watchers": assignment.get("watchers") or [],
            "case_type": new_case_data.get("case_type") or "Oversight",
            "case_subtype": new_case_data.get("case_subtype") or None,
            "impact_summary": new_case_data.get("impact_summary") or new_case_data.get("summary") or signal.get("summary"),
            "handling_strategy": new_case_data.get("handling_strategy") or "direct",
            "related_case_id": new_case_data.get("related_case_id") or None,
            "case_relationship": new_case_data.get("case_relationship") or None,
            "blockers": [],
            "created_at": _now(),
            "updated_at": _now(),
        }
        sd.CASES.append(case)
        sd.CASE_BY_ID[cid] = case
        persistence.persist("case", case)
        # _merge_assessment already layers `override` onto initial_assessment()
        # and adds the phase-2 risk scoring, so it supersedes the old dict spread.
        assess = _merge_assessment(signal_id, override)
        if assignment.get("recommended_action"):
            assess["recommended_action"] = assignment["recommended_action"]
        _register_risk(
            cid,
            vendor,
            assess,
            region=region,
            vendor_name=manual_vendor_name or vendor["name"],
        )
        signal["case_id"] = cid
        signal["status"] = "Terhubung ke Kasus"
        signal["issue_category"] = case["issue_category"]
        persistence.persist("signal", signal)

        audit.append(_add_audit(cid, "case_created",
                                f"Kasus {sd.case_number(cid)} dibentuk dari sinyal #{signal_id}.",
                                actor=actor))
        audit.append(_add_audit(
            cid, "case_monitoring_started",
            "Kasus langsung berstatus Open & Monitored dan dapat ditangani tanpa tiket.", actor=actor,
        ))
        audit.append(_add_audit(
            cid, "location_updated",
            f"Lokasi kasus ditetapkan. Sebelum: dari sinyal; sesudah: {region} → {district} → {school}.",
            actor=actor,
        ))
        if requested_vendor_id == MANUAL_VENDOR_ID:
            audit.append(_add_audit(
                cid, "vendor_entered_from_report",
                f"Penyedia dimasukkan dari laporan. Sebelum: Belum teridentifikasi; sesudah: {manual_vendor_name}. "
                f"Catatan sumber: {case['vendor_source_note'] or '-'}.", actor=actor,
            ))
        elif vendor_id == "vnd-unknown":
            audit.append(_add_audit(
                cid, "vendor_marked_unidentified",
                "Penyedia tetap Belum teridentifikasi; operator tidak dipaksa memilih vendor acak.", actor=actor,
            ))
        else:
            audit.append(_add_audit(
                cid, "vendor_candidate_selected",
                f"Kandidat penyedia dipilih. Sebelum: Belum teridentifikasi; sesudah: {vendor['name']}. "
                "Kandidat berdasarkan cakupan layanan wilayah; konfirmasi operator tetap diperlukan.", actor=actor,
            ))
        # Lampiran laporan resmi menjadi bukti utama kasus.
        ev = _add_evidence_from_signal(cid, signal)
        if ev:
            audit.append(_add_audit(cid, "evidence_added",
                                    f"Bukti '{ev['title']}' (sumber {ev['source']}) ditambahkan dari sinyal #{signal_id}. "
                                    f"Status: Perlu Ditinjau.", actor=actor))
        if override.get("operator_adjusted"):
            audit.append(_add_audit(cid, "risk_overridden",
                                    f"Prioritas disesuaikan operator menjadi {override['priority_label']} "
                                    f"(skor {override['final_priority_score']}). Alasan: {override.get('override_reason', '-')}."))
        if assignment.get("investigator"):
            audit.append(_add_audit(cid, "investigator_assigned",
                                    f"Investigator ditetapkan. Sebelum: Belum ditetapkan; sesudah: {assignment['investigator']}. "
                                    f"Urgensi {assignment.get('urgency', '-')}, SLA usulan {assignment.get('sla', '-')}.",
                                    actor=actor))
        if assignment.get("unit"):
            audit.append(_add_audit(
                cid, "responsible_unit_assigned",
                f"Unit penanggung jawab ditetapkan. Sebelum: Belum ditetapkan; sesudah: {assignment['unit']}.",
                actor=actor,
            ))
        # Sinyal/bukti terkait yang dicentang ikut ditautkan ke kasus baru.
        extra_linked, extra_evidence_ids = _link_selected_items(case, extra_signals, extra_evidence, audit, actor)
        from app.services.copilot.service import index_case_for_copilot
        index_case_for_copilot(cid)
        # Tidak membuat tiket otomatis.
        return {"outcome": "created", "case_id": cid, "case_number": sd.case_number(cid),
                "redirect": f"/cases/{cid}", "audit_events": audit,
                "linked_signal_ids": [signal_id, *extra_linked],
                "added_evidence_ids": ([ev["id"]] if ev else []) + extra_evidence_ids,
                "case": _case_snapshot(cid), "ai_notice": sd.GOVERNANCE_NOTICE}

    if decision == "defer":
        signal["status"] = "Perlu Ditinjau"
        note = payload.get("defer_reason")
        if not note:
            raise HTTPException(status_code=422, detail="Alasan/catatan reviewer wajib diisi saat menunda.")
        signal["reviewer_note"] = note
        persistence.persist("signal", signal)
        audit.append(_add_audit(None, "review_deferred",
                                f"Sinyal #{signal_id} disimpan sebagai perlu ditinjau. Catatan: {note}."))
        return {"outcome": "deferred", "signal_id": signal_id,
                "redirect": "/intake", "audit_events": audit, "ai_notice": sd.GOVERNANCE_NOTICE}

    raise HTTPException(status_code=422, detail=f"Keputusan tidak dikenal: {decision}")


UNLINK_GOVERNANCE = (
    "Melepaskan signal tidak menghapus data sumber; tindakan ini hanya mengakhiri "
    "hubungan signal dengan kasus dan dicatat pada jejak audit."
)


def unlink_signal(signal_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Lepaskan relasi signal→kasus; signal kembali ke antrean 'Perlu Ditinjau'.

    Tidak menghapus aset gambar fisik maupun audit lama. Bukti yang HANYA
    berasal dari signal ini ditandai 'Dilepas dari kasus'. Bukti yang dipakai
    signal lain tidak dilepas.
    """
    signal = get_signal(signal_id)
    case_id = signal.get("case_id")
    if not case_id:
        raise HTTPException(status_code=409, detail="Sinyal tidak sedang terhubung ke kasus.")
    reason = (payload.get("reason") or "").strip()
    if not reason:
        raise HTTPException(status_code=422, detail="Alasan pelepasan wajib diisi.")

    case = sd.CASE_BY_ID.get(case_id)
    actor = "Operator Demo"
    audit: list[dict[str, Any]] = []

    # Bukti yang sumbernya semata-mata signal ini.
    other_linked_signals = {
        s["id"] for s in all_signals() if s["id"] != signal_id and s.get("case_id") == case_id
    }
    unlinked_ev_ids: list[int] = []
    for ev in sd.EVIDENCE:
        if ev.get("case_id") != case_id or ev.get("unlinked_from_case"):
            continue
        ev_signal = ev.get("signal_id")
        if ev_signal == signal_id and ev_signal not in other_linked_signals:
            ev["unlinked_from_case"] = True
            ev["review_status"] = "Dilepas dari kasus"
            persistence.persist("evidence", ev)
            unlinked_ev_ids.append(ev["id"])
            ticket = sd.TICKET_BY_CASE.get(case_id)
            if ticket and ev["id"] in ticket.get("linked_evidence_ids", []):
                ticket["linked_evidence_ids"].remove(ev["id"])
                persistence.persist("ticket", ticket)

    # Putuskan relasi signal.
    signal["case_id"] = None
    signal["status"] = "Perlu Ditinjau"
    persistence.persist("signal", signal)

    audit.append(_add_audit(
        case_id, "signal_unlinked",
        f"Operator {actor} melepaskan sinyal #{signal_id} dari {sd.case_number(case_id)}. "
        f"Alasan: {reason}. Data sumber dan aset tidak dihapus.",
        actor=actor,
    ))
    for ev_id in unlinked_ev_ids:
        audit.append(_add_audit(
            case_id, "evidence_unlinked",
            f"Bukti #{ev_id} ditandai 'Dilepas dari kasus' karena berasal dari sinyal #{signal_id}. Aset tidak dihapus.",
            actor=actor,
        ))
    if case is not None:
        case["updated_at"] = _now()
        persistence.persist("case", case)

    return {
        "outcome": "unlinked",
        "signal_id": signal_id,
        "case_id": case_id,
        "case_number": sd.case_number(case_id),
        "unlinked_evidence_ids": unlinked_ev_ids,
        "audit_events": audit,
        "case": _case_snapshot(case_id) if case is not None else None,
        "ai_notice": UNLINK_GOVERNANCE,
    }
