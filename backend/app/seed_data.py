"""Sumber data kanonik MonitorMBG (dwibahasa istilah, isi Bahasa Indonesia).

SATU sumber kebenaran untuk seluruh prototype:
- ``demo_data.py`` menyusun respons API dari modul ini.
- ``seed.py`` memuat data yang sama ke PostgreSQL.
- ``frontend/src/lib/demoFallback.ts`` adalah cermin identik untuk mode offline.

Semua data fiktif, aman-privasi. Skor CV/OCR/NLP adalah sinyal
pra-verifikasi untuk ditinjau operator, bukan temuan otomatis atau
keputusan final. Foto adalah bukti pra-verifikasi, bukan bukti pelanggaran.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# Catatan tata kelola dipakai di semua permukaan hasil penilaian.
GOVERNANCE_NOTICE = (
    "Data dan analisis pada halaman ini merupakan sinyal pra-verifikasi untuk "
    "membantu prioritisasi. Verifikasi lapangan dan keputusan akhir tetap "
    "dilakukan oleh operator berwenang."
)


def _ts(day: int, hour: int, minute: int = 0) -> str:
    return datetime(2026, 6, day, hour, minute, tzinfo=timezone.utc).isoformat()


def case_number(case_id: str) -> str:
    """`case-001` -> `MBG-001` (nomor ramah pengguna)."""
    digits = "".join(ch for ch in case_id if ch.isdigit()) or "000"
    return f"MBG-{digits}"


# Basis path aset foto (dipakai frontend & mount statis backend).
EVIDENCE_MEDIA_BASE = "/evidence-media"


# ── Vendor / SPPG ────────────────────────────────────────────────────────
VENDORS: list[dict[str, Any]] = [
    {
        "id": "vnd-001",
        "name": "SPPG Nusantara Sehat",
        "region": "DKI Jakarta",
        "district": "Jakarta Timur",
        "assigned_schools": ["SDN Melati 03", "SMPN 182 Jakarta", "SDN Rawamangun 07"],
        "daily_meal_volume": 3280,
        "compliance_status": "Sedang Ditinjau",
        "risk_score": 88,
        "risk_trend": [62, 68, 74, 81, 88],
        "watchlist_status": "Kritis",
        "watchlist_reason": "Aduan porsi protein rendah berulang, keterlambatan distribusi, dan indikasi foto duplikat.",
        "last_inspection_date": "2026-05-29",
        "repeated_issue_categories": ["porsi protein kurang", "keterlambatan distribusi", "indikasi foto duplikat"],
        "coverage_notes": "Klaster tiga sekolah di Jakarta Timur; kepadatan sinyal publik tinggi pekan ini.",
        "recommended_action": "Minta klarifikasi vendor dan jadwalkan verifikasi lapangan.",
    },
    {
        "id": "vnd-002",
        "name": "Dapur Sehat Bandung Raya",
        "region": "Jawa Barat",
        "district": "Kota Bandung",
        "assigned_schools": ["SDN Sukajadi 05", "SMPN 12 Bandung"],
        "daily_meal_volume": 2410,
        "compliance_status": "Perlu Verifikasi",
        "risk_score": 79,
        "risk_trend": [52, 56, 63, 72, 79],
        "watchlist_status": "Tinggi",
        "watchlist_reason": "Kekhawatiran higiene dan indikasi gejala keracunan dari dua kanal independen.",
        "last_inspection_date": "2026-05-25",
        "repeated_issue_categories": ["kekhawatiran higiene", "indikasi keracunan makanan", "makanan dingin"],
        "coverage_notes": "Dua sekolah berdekatan melaporkan gejala serupa dalam 48 jam.",
        "recommended_action": "Koordinasikan inspeksi dinas kesehatan dan tingkatkan sampling sementara.",
    },
    {
        "id": "vnd-003",
        "name": "SPPG Pangan Aman Semarang",
        "region": "Jawa Tengah",
        "district": "Kota Semarang",
        "assigned_schools": ["SDN Tembalang 01", "SMPN 21 Semarang"],
        "daily_meal_volume": 1980,
        "compliance_status": "Sesuai",
        "risk_score": 34,
        "risk_trend": [38, 36, 34, 33, 34],
        "watchlist_status": "Rendah",
        "watchlist_reason": "Pemantauan rutin saja.",
        "last_inspection_date": "2026-05-31",
        "repeated_issue_categories": ["dokumentasi belum lengkap"],
        "coverage_notes": "Operasional stabil dengan sedikit celah dokumentasi.",
        "recommended_action": "Minta pelengkapan checklist distribusi pada laporan harian berikutnya.",
    },
    {
        "id": "vnd-004",
        "name": "Dapur Mandiri Surabaya Timur",
        "region": "Jawa Timur",
        "district": "Surabaya",
        "assigned_schools": ["SDN Rungkut Menanggal", "SMPN 35 Surabaya"],
        "daily_meal_volume": 2875,
        "compliance_status": "Dieskalasi",
        "risk_score": 83,
        "risk_trend": [55, 61, 70, 77, 83],
        "watchlist_status": "Kritis",
        "watchlist_reason": "Anomali biaya, buah/susu tidak lengkap, dan ketidaksesuaian menu berulang.",
        "last_inspection_date": "2026-05-22",
        "repeated_issue_categories": ["anomali biaya", "buah/susu tidak lengkap", "ketidaksesuaian menu"],
        "coverage_notes": "Biaya per porsi dilaporkan di atas patokan sementara kelengkapan menu menurun.",
        "recommended_action": "Eskalasikan ke tinjauan pengadaan dan lakukan verifikasi menu.",
    },
    {
        "id": "vnd-005",
        "name": "SPPG Cerdas Gizi Medan",
        "region": "Sumatera Utara",
        "district": "Kota Medan",
        "assigned_schools": ["SDN Medan Johor 09", "SMPN 28 Medan"],
        "daily_meal_volume": 1740,
        "compliance_status": "Sesuai",
        "risk_score": 41,
        "risk_trend": [43, 39, 40, 42, 41],
        "watchlist_status": "Sedang",
        "watchlist_reason": "Aduan makanan dingin masih di bawah ambang eskalasi.",
        "last_inspection_date": "2026-05-30",
        "repeated_issue_categories": ["makanan dingin", "keterlambatan distribusi"],
        "coverage_notes": "Isu tampak operasional, bukan terkait kecurangan bukti.",
        "recommended_action": "Pantau waktu rute distribusi selama satu pekan.",
    },
    {
        "id": "vnd-006",
        "name": "Dapur Prima Makassar",
        "region": "Sulawesi Selatan",
        "district": "Makassar",
        "assigned_schools": ["SDN Panakkukang 02", "SMPN 8 Makassar"],
        "daily_meal_volume": 2135,
        "compliance_status": "Perlu Verifikasi",
        "risk_score": 67,
        "risk_trend": [45, 51, 56, 63, 67],
        "watchlist_status": "Tinggi",
        "watchlist_reason": "Dokumentasi belum lengkap dan paket bukti berkeyakinan rendah.",
        "last_inspection_date": "2026-05-27",
        "repeated_issue_categories": ["dokumentasi belum lengkap", "ketidaksesuaian menu"],
        "coverage_notes": "Foto laporan harian lengkap tetapi hasil OCR faktur lemah.",
        "recommended_action": "Minta faktur perbaikan dan tinjauan operator atas bukti.",
    },
    {
        "id": "vnd-007",
        "name": "SPPG Sejahtera Denpasar",
        "region": "Bali",
        "district": "Denpasar",
        "assigned_schools": ["SDN Renon 04", "SMPN 10 Denpasar"],
        "daily_meal_volume": 1320,
        "compliance_status": "Sesuai",
        "risk_score": 28,
        "risk_trend": [31, 30, 29, 27, 28],
        "watchlist_status": "Rendah",
        "watchlist_reason": "Tidak ada isu berisiko tinggi berulang.",
        "last_inspection_date": "2026-06-01",
        "repeated_issue_categories": [],
        "coverage_notes": "Vendor stabil dengan dokumentasi harian lengkap.",
        "recommended_action": "Lanjutkan pemantauan rutin.",
    },
    {
        "id": "vnd-008",
        "name": "Dapur Anak Hebat Yogyakarta",
        "region": "DI Yogyakarta",
        "district": "Sleman",
        "assigned_schools": ["SDN Condongcatur 02", "SMPN 4 Sleman"],
        "daily_meal_volume": 1565,
        "compliance_status": "Sedang Ditinjau",
        "risk_score": 58,
        "risk_trend": [35, 42, 46, 53, 58],
        "watchlist_status": "Sedang",
        "watchlist_reason": "Laporan buah tidak lengkap meningkat dan satu lonjakan anomali publik.",
        "last_inspection_date": "2026-05-28",
        "repeated_issue_categories": ["buah/susu tidak lengkap", "dokumentasi belum lengkap"],
        "coverage_notes": "Tren terkini meningkat namun keyakinan bukti sedang.",
        "recommended_action": "Tinjau tiga laporan harian berikutnya dan konfirmasi substitusi menu.",
    },
    {
        "id": "vnd-009",
        "name": "SPPG Banten Tangerang Sehat",
        "region": "Banten",
        "district": "Kota Tangerang",
        "assigned_schools": ["SDN Tangerang 01", "SMPN 4 Tangerang"],
        "daily_meal_volume": 1860,
        "compliance_status": "Perlu Verifikasi",
        "risk_score": 48,
        "risk_trend": [42, 44, 46, 47, 48],
        "watchlist_status": "Sedang",
        "watchlist_reason": "Kandidat registry demo untuk cakupan Kota Tangerang.",
        "last_inspection_date": "2026-05-26",
        "repeated_issue_categories": ["dokumentasi belum lengkap"],
        "coverage_notes": "Cakupan demo terbatas pada Kota Tangerang dan sekolah yang tercantum.",
        "recommended_action": "Konfirmasi cakupan layanan dan minta dokumen operasional terbaru.",
    },
    {
        "id": "vnd-010",
        "name": "SPPG Tanggamus Pangan Aman",
        "region": "Lampung",
        "district": "Kabupaten Tanggamus",
        "assigned_schools": ["SDN 1 Karang Agung", "SDN Kota Agung 02"],
        "daily_meal_volume": 1240,
        "compliance_status": "Perlu Verifikasi",
        "risk_score": 46,
        "risk_trend": [40, 42, 43, 45, 46],
        "watchlist_status": "Sedang",
        "watchlist_reason": "Kandidat registry demo; bukan penetapan vendor pada laporan belatung.",
        "last_inspection_date": "2026-05-24",
        "repeated_issue_categories": ["dokumentasi belum lengkap"],
        "coverage_notes": "Kandidat fiktif dengan cakupan Kabupaten Tanggamus; perlu konfirmasi operator.",
        "recommended_action": "Konfirmasi identitas penyedia sebelum verifikasi lapangan.",
    },
    {
        "id": "vnd-011",
        "name": "Dapur Lampung Lintas Kabupaten",
        "region": "Lampung",
        "district": "Kota Bandar Lampung",
        "assigned_schools": ["SDN 1 Karang Agung", "SDN Bandar Lampung 03"],
        "daily_meal_volume": 1680,
        "compliance_status": "Perlu Verifikasi",
        "risk_score": 44,
        "risk_trend": [39, 40, 42, 43, 44],
        "watchlist_status": "Sedang",
        "watchlist_reason": "Kandidat registry demo dengan cakupan lintas kabupaten di Lampung.",
        "last_inspection_date": "2026-05-23",
        "repeated_issue_categories": ["keterlambatan distribusi"],
        "coverage_notes": "Kandidat fiktif; cakupan Tanggamus harus dikonfirmasi operator.",
        "recommended_action": "Minta klarifikasi cakupan dan penanggung jawab wilayah.",
    },
    {
        "id": "vnd-012",
        "name": "SPPG Sumsel Palembang Bersama",
        "region": "Sumatera Selatan",
        "district": "Kota Palembang",
        "assigned_schools": ["SDN Palembang 07", "SMPN 18 Palembang"],
        "daily_meal_volume": 1720,
        "compliance_status": "Sesuai",
        "risk_score": 43,
        "risk_trend": [40, 41, 42, 42, 43],
        "watchlist_status": "Rendah",
        "watchlist_reason": "Pemantauan rutin pada cakupan Kota Palembang.",
        "last_inspection_date": "2026-05-28",
        "repeated_issue_categories": ["dokumentasi belum lengkap"],
        "coverage_notes": "Cakupan demo terbatas pada Kota Palembang.",
        "recommended_action": "Lanjutkan pemantauan rutin dan validasi dokumen.",
    },
    {
        "id": "vnd-013",
        "name": "Dapur Kepri Batam Sejahtera",
        "region": "Kepulauan Riau",
        "district": "Kota Batam",
        "assigned_schools": ["SDN Batam 01", "SMPN 7 Batam"],
        "daily_meal_volume": 1480,
        "compliance_status": "Sesuai",
        "risk_score": 39,
        "risk_trend": [37, 38, 38, 39, 39],
        "watchlist_status": "Rendah",
        "watchlist_reason": "Pemantauan rutin; Kepri adalah provinsi terpisah dari DKI Jakarta.",
        "last_inspection_date": "2026-05-29",
        "repeated_issue_categories": [],
        "coverage_notes": "Cakupan demo terbatas pada Kota Batam, Kepulauan Riau.",
        "recommended_action": "Lanjutkan pemantauan rutin.",
    },
]

VENDOR_BY_ID = {v["id"]: v for v in VENDORS}

# Vendor placeholder untuk kasus yang dibentuk dari sinyal tanpa vendor jelas.
# Tidak dimasukkan ke daftar VENDORS (agar metrik watchlist/heatmap tidak berubah),
# hanya dapat di-resolve lewat VENDOR_BY_ID saat membangun kasus.
UNIDENTIFIED_VENDOR = {
    "id": "vnd-unknown",
    "name": "Belum teridentifikasi",
    "region": "Belum teridentifikasi",
    "district": "Belum teridentifikasi",
    "assigned_schools": ["Belum teridentifikasi"],
    "daily_meal_volume": 0,
    "compliance_status": "Perlu Verifikasi",
    "risk_score": 0,
    "risk_trend": [0, 0, 0, 0, 0],
    "watchlist_status": "Rendah",
    "watchlist_reason": "Vendor belum teridentifikasi dari sinyal.",
    "last_inspection_date": "-",
    "repeated_issue_categories": [],
    "coverage_notes": "Vendor perlu diidentifikasi melalui klarifikasi awal.",
    "recommended_action": "Minta klarifikasi awal untuk mengidentifikasi vendor dan lokasi.",
}
VENDOR_BY_ID[UNIDENTIFIED_VENDOR["id"]] = UNIDENTIFIED_VENDOR

# Koordinat kabupaten/kota untuk heatmap (indeks selaras VENDORS).
_LATLNG = [
    (-6.2088, 106.8456), (-6.9175, 107.6191), (-6.9667, 110.4167), (-7.2575, 112.7521),
    (3.5952, 98.6722), (-5.1477, 119.4327), (-8.6705, 115.2126), (-7.7956, 110.3695),
    (-6.1783, 106.6319), (-5.4667, 104.6167), (-5.4292, 105.2610), (-2.9909, 104.7566),
    (1.0456, 104.0305),
]


# ── Registry lokasi & penugasan ──────────────────────────────────────────
# Mapping ini adalah sumber kanonik filter dropdown. Kepri sengaja berdiri
# sebagai provinsi sendiri dan tidak pernah dipetakan ke DKI Jakarta.
LOCATION_REGISTRY: list[dict[str, Any]] = [
    {"province": "DKI Jakarta", "districts": [
        {"name": "Jakarta Pusat", "schools": ["SDN Menteng 01"], "vendor_ids": []},
        {"name": "Jakarta Barat", "schools": ["SDN Palmerah 05"], "vendor_ids": []},
        {"name": "Jakarta Selatan", "schools": ["SDN Tebet 03"], "vendor_ids": []},
        {"name": "Jakarta Timur", "schools": ["SDN Melati 03", "SMPN 182 Jakarta", "SDN Rawamangun 07"], "vendor_ids": ["vnd-001"]},
        {"name": "Jakarta Utara", "schools": ["SDN Kelapa Gading 02"], "vendor_ids": []},
        {"name": "Kepulauan Seribu", "schools": ["SDN Pulau Pramuka 01"], "vendor_ids": []},
    ]},
    {"province": "Banten", "districts": [
        {"name": "Kota Tangerang", "schools": ["SDN Tangerang 01", "SMPN 4 Tangerang"], "vendor_ids": ["vnd-009"]},
    ]},
    {"province": "Jawa Barat", "districts": [
        {"name": "Kota Bandung", "schools": ["SDN Sukajadi 05", "SMPN 12 Bandung"], "vendor_ids": ["vnd-002"]},
    ]},
    {"province": "Jawa Tengah", "districts": [
        {"name": "Kota Semarang", "schools": ["SDN Tembalang 01", "SMPN 21 Semarang"], "vendor_ids": ["vnd-003"]},
    ]},
    {"province": "DI Yogyakarta", "districts": [
        {"name": "Sleman", "schools": ["SDN Condongcatur 02", "SMPN 4 Sleman"], "vendor_ids": ["vnd-008"]},
    ]},
    {"province": "Jawa Timur", "districts": [
        {"name": "Surabaya", "schools": ["SDN Rungkut Menanggal", "SMPN 35 Surabaya"], "vendor_ids": ["vnd-004"]},
    ]},
    {"province": "Bali", "districts": [
        {"name": "Denpasar", "schools": ["SDN Renon 04", "SMPN 10 Denpasar"], "vendor_ids": ["vnd-007"]},
    ]},
    {"province": "Lampung", "districts": [
        {"name": "Kabupaten Tanggamus", "schools": ["SDN 1 Karang Agung", "SDN Kota Agung 02"], "vendor_ids": ["vnd-010", "vnd-011"]},
        {"name": "Kota Bandar Lampung", "schools": ["SDN Bandar Lampung 03"], "vendor_ids": ["vnd-011"]},
    ]},
    {"province": "Sumatera Utara", "districts": [
        {"name": "Kota Medan", "schools": ["SDN Medan Johor 09", "SMPN 28 Medan"], "vendor_ids": ["vnd-005"]},
    ]},
    {"province": "Sumatera Selatan", "districts": [
        {"name": "Kota Palembang", "schools": ["SDN Palembang 07", "SMPN 18 Palembang"], "vendor_ids": ["vnd-012"]},
    ]},
    {"province": "Sulawesi Selatan", "districts": [
        {"name": "Makassar", "schools": ["SDN Panakkukang 02", "SMPN 8 Makassar"], "vendor_ids": ["vnd-006"]},
    ]},
    {"province": "Kepulauan Riau", "districts": [
        {"name": "Kota Batam", "schools": ["SDN Batam 01", "SMPN 7 Batam"], "vendor_ids": ["vnd-013"]},
    ]},
]

INVESTIGATOR_REGISTRY: list[dict[str, Any]] = [
    {"id": "inv-operator-dewi", "name": "Operator Dewi", "role": "Operator nasional", "provinces": [], "districts": [], "national": True},
    {"id": "inv-jakarta-timur", "name": "Tim Verifikasi Lapangan Jakarta Timur", "role": "Verifikasi lapangan", "provinces": ["DKI Jakarta"], "districts": ["Jakarta Timur"], "national": False},
    {"id": "inv-tanggamus", "name": "Operator Pengawasan Tanggamus", "role": "Pengawasan kabupaten", "provinces": ["Lampung"], "districts": ["Kabupaten Tanggamus"], "national": False},
    {"id": "inv-lampung-field", "name": "Tim Verifikasi Lapangan Lampung", "role": "Verifikasi lapangan", "provinces": ["Lampung"], "districts": [], "national": False},
    {"id": "inv-lampung-nutrition", "name": "Tim Gizi dan Kepatuhan Lampung", "role": "Gizi dan kepatuhan", "provinces": ["Lampung"], "districts": [], "national": False},
    {"id": "inv-vendor", "name": "Unit Pengawasan Vendor", "role": "Pengawasan vendor lintas wilayah", "provinces": [], "districts": [], "national": True},
    {"id": "inv-nutrition", "name": "Tim Gizi dan Kepatuhan", "role": "Gizi dan kepatuhan lintas wilayah", "provinces": [], "districts": [], "national": True},
]

UNIT_REGISTRY: list[dict[str, Any]] = [
    {"id": "unit-national", "name": "Unit Pengawasan Vendor MBG Nasional", "role": "Koordinasi nasional", "provinces": [], "districts": [], "national": True},
    {"id": "unit-vendor", "name": "Unit Pengawasan Vendor MBG", "role": "Pengawasan vendor lintas wilayah", "provinces": [], "districts": [], "national": True},
    {"id": "unit-jakarta-timur", "name": "Dinas Kesehatan Jakarta Timur", "role": "Kesehatan wilayah", "provinces": ["DKI Jakarta"], "districts": ["Jakarta Timur"], "national": False},
    {"id": "unit-tanggamus-health", "name": "Dinas Kesehatan Kabupaten Tanggamus", "role": "Kesehatan kabupaten", "provinces": ["Lampung"], "districts": ["Kabupaten Tanggamus"], "national": False},
    {"id": "unit-lampung-vendor", "name": "Unit Pengawasan Vendor MBG Lampung", "role": "Pengawasan vendor provinsi", "provinces": ["Lampung"], "districts": [], "national": False},
    {"id": "unit-lampung-food", "name": "Tim Respons Keamanan Pangan Lampung", "role": "Respons keamanan pangan", "provinces": ["Lampung"], "districts": [], "national": False},
    {"id": "unit-nutrition", "name": "Tim Gizi dan Kepatuhan", "role": "Gizi dan kepatuhan lintas wilayah", "provinces": [], "districts": [], "national": True},
    {"id": "unit-procurement", "name": "Meja Tinjauan Pengadaan", "role": "Tinjauan pengadaan lintas wilayah", "provinces": [], "districts": [], "national": True},
]

ASSIGNMENT_GOVERNANCE_NOTICE = (
    "Kandidat penyedia dan penugasan disaring berdasarkan cakupan wilayah sebagai bantuan pra-verifikasi. "
    "Operator berwenang tetap mengonfirmasi keterkaitan dan tindakan lanjutan."
)


# ── Kasus (10, tetap) ────────────────────────────────────────────────────
# Setiap kasus menunjuk satu vendor. `case-001` adalah golden path.
CASES: list[dict[str, Any]] = [
    {
        "case_id": "case-001", "vendor_id": "vnd-001", "school": "SDN Melati 03",
        "issue_category": "porsi protein kurang", "priority_label": "Tinggi",
        "status": "Sedang Ditinjau",
        "title": "Indikasi porsi protein kurang dan keterlambatan distribusi di SDN Melati 03",
        "created_at": _ts(2, 8, 15), "updated_at": _ts(4, 15, 30),
    },
    {
        "case_id": "case-002", "vendor_id": "vnd-002", "school": "SDN Sukajadi 05",
        "issue_category": "indikasi keracunan makanan", "priority_label": "Kritis",
        "status": "Verifikasi Lapangan Terjadwal",
        "title": "Indikasi keracunan makanan di SDN Sukajadi 05",
        "created_at": _ts(2, 10, 15), "updated_at": _ts(4, 12, 0),
    },
    {
        "case_id": "case-003", "vendor_id": "vnd-004", "school": "SDN Rungkut Menanggal",
        "issue_category": "anomali biaya", "priority_label": "Kritis",
        "status": "Menunggu Klarifikasi Vendor",
        "title": "Anomali biaya per porsi di SDN Rungkut Menanggal",
        "created_at": _ts(1, 9, 20), "updated_at": _ts(4, 11, 0),
    },
    {
        "case_id": "case-004", "vendor_id": "vnd-006", "school": "SDN Panakkukang 02",
        "issue_category": "dokumentasi belum lengkap", "priority_label": "Tinggi",
        "status": "Menunggu Klarifikasi Vendor",
        "title": "Dokumentasi dan faktur belum lengkap di SDN Panakkukang 02",
        "created_at": _ts(1, 8, 40), "updated_at": _ts(3, 16, 0),
    },
    {
        "case_id": "case-005", "vendor_id": "vnd-008", "school": "SDN Condongcatur 02",
        "issue_category": "buah/susu tidak lengkap", "priority_label": "Sedang",
        "status": "Sedang Ditinjau",
        "title": "Laporan buah/susu tidak lengkap di SDN Condongcatur 02",
        "created_at": _ts(2, 9, 5), "updated_at": _ts(3, 14, 0),
    },
    {
        "case_id": "case-006", "vendor_id": "vnd-005", "school": "SDN Medan Johor 09",
        "issue_category": "makanan dingin", "priority_label": "Sedang",
        "status": "Sedang Ditinjau",
        "title": "Aduan makanan dingin dan keterlambatan di SDN Medan Johor 09",
        "created_at": _ts(3, 8, 10), "updated_at": _ts(3, 13, 0),
    },
    {
        "case_id": "case-007", "vendor_id": "vnd-004", "school": "SMPN 35 Surabaya",
        "issue_category": "ketidaksesuaian menu", "priority_label": "Tinggi",
        "status": "Menunggu Klarifikasi Vendor",
        "title": "Ketidaksesuaian menu aktual dengan rencana di SMPN 35 Surabaya",
        "created_at": _ts(2, 7, 30), "updated_at": _ts(4, 9, 0),
    },
    {
        "case_id": "case-008", "vendor_id": "vnd-002", "school": "SMPN 12 Bandung",
        "issue_category": "kekhawatiran higiene", "priority_label": "Tinggi",
        "status": "Verifikasi Lapangan Terjadwal",
        "title": "Kekhawatiran higiene dapur di SMPN 12 Bandung",
        "created_at": _ts(3, 7, 45), "updated_at": _ts(4, 10, 0),
    },
    {
        "case_id": "case-009", "vendor_id": "vnd-003", "school": "SDN Tembalang 01",
        "issue_category": "dokumentasi belum lengkap", "priority_label": "Rendah",
        "status": "Selesai",
        "title": "Checklist distribusi belum lengkap di SDN Tembalang 01",
        "created_at": _ts(1, 8, 0), "updated_at": _ts(4, 17, 0),
    },
    {
        "case_id": "case-010", "vendor_id": "vnd-007", "school": "SDN Renon 04",
        "issue_category": "keterlambatan distribusi", "priority_label": "Rendah",
        "status": "Selesai",
        "title": "Keterlambatan distribusi terisolasi di SDN Renon 04",
        "created_at": _ts(1, 9, 0), "updated_at": _ts(3, 12, 0),
    },
]

CASE_BY_ID = {c["case_id"]: c for c in CASES}


# ── Signal (intake) ──────────────────────────────────────────────────────
# Setiap signal WAJIB punya case_id valid ATAU case_id=None ("belum dibentuk
# kasus"). Tidak ada case_id yang menunjuk kasus tidak tersedia.
SIGNALS: list[dict[str, Any]] = [
    # case-001 (golden path) — 3 signal
    {
        "id": 1, "case_id": "case-001", "source": "Aduan Wali Murid",
        "source_confidence": 0.64, "urgency": "Tinggi", "status": "Terhubung ke Kasus",
        "summary": "Porsi lauk kecil dan makanan datang terlambat di SDN Melati 03",
        "text": ("Menu hari ini hanya nasi, sedikit sayur, dan lauk telur sangat kecil. "
                 "Makanan juga datang terlambat sekitar 45 menit."),
        "created_at": _ts(2, 8, 15),
    },
    {
        "id": 2, "case_id": "case-001", "source": "Laporan Pengawas",
        "source_confidence": 0.72, "urgency": "Tinggi", "status": "Terhubung ke Kasus",
        "summary": "Pengawas melaporkan pola porsi protein rendah yang berulang di SPPG Nusantara Sehat",
        "text": ("Laporan pengawas: pola keterlambatan dan porsi protein rendah berulang "
                 "pada distribusi MBG oleh SPPG Nusantara Sehat."),
        "created_at": _ts(3, 9, 30),
    },
    {
        "id": 3, "case_id": "case-001", "source": "Laporan Harian Vendor",
        "source_confidence": 0.70, "urgency": "Sedang", "status": "Terhubung ke Kasus",
        "summary": "Laporan harian vendor: menu aktual nasi, telur, sayur (tanpa buah/susu)",
        "text": ("Laporan harian vendor mencatat menu aktual nasi, telur kecil, sayur; "
                 "buah dan susu pada rencana menu tidak tercatat terdistribusi."),
        "created_at": _ts(4, 8, 0),
    },
    # case-002 — 2 signal
    {
        "id": 4, "case_id": "case-002", "source": "Hotline Sekolah",
        "source_confidence": 0.81, "urgency": "Tinggi", "status": "Terhubung ke Kasus",
        "summary": "Beberapa siswa bergejala mual setelah makan siang di SDN Sukajadi 05",
        "text": "Aduan gejala mual dan pusing pada beberapa siswa setelah distribusi MBG.",
        "created_at": _ts(2, 10, 15),
    },
    {
        "id": 5, "case_id": "case-002", "source": "Laporan Komunitas",
        "source_confidence": 0.66, "urgency": "Tinggi", "status": "Terhubung ke Kasus",
        "summary": "Sekolah berdekatan melaporkan gejala serupa dalam 48 jam",
        "text": "Laporan komunitas menyebut gejala serupa di sekolah lain dalam wilayah yang sama.",
        "created_at": _ts(3, 8, 40),
    },
    # case-003 — 2 signal
    {
        "id": 6, "case_id": "case-003", "source": "Laporan Harian Vendor",
        "source_confidence": 0.58, "urgency": "Sedang", "status": "Sedang Ditinjau",
        "summary": "Biaya per porsi di atas patokan pada laporan harian Dapur Mandiri Surabaya Timur",
        "text": "Laporan harian mencatat biaya per porsi di atas patokan anggaran standar.",
        "created_at": _ts(1, 9, 20),
    },
    {
        "id": 7, "case_id": "case-003", "source": "Tinjauan Pengadaan",
        "source_confidence": 0.74, "urgency": "Tinggi", "status": "Terhubung ke Kasus",
        "summary": "Tinjauan pengadaan menandai selisih biaya sementara kelengkapan menu menurun",
        "text": "Tim pengadaan menandai anomali biaya yang perlu klarifikasi vendor.",
        "created_at": _ts(2, 11, 0),
    },
    # case-004 — 2 signal
    {
        "id": 8, "case_id": "case-004", "source": "Laporan Harian Vendor",
        "source_confidence": 0.52, "urgency": "Sedang", "status": "Sedang Ditinjau",
        "summary": "Faktur pada laporan harian Dapur Prima Makassar sulit terbaca (OCR lemah)",
        "text": "Bidang faktur pada laporan harian terbaca sebagian; total biaya perlu konfirmasi.",
        "created_at": _ts(1, 8, 40),
    },
    {
        "id": 9, "case_id": "case-004", "source": "Operator Sekolah",
        "source_confidence": 0.60, "urgency": "Sedang", "status": "Terhubung ke Kasus",
        "summary": "Operator sekolah melaporkan checklist distribusi belum lengkap",
        "text": "Operator sekolah mencatat beberapa item checklist distribusi belum terisi.",
        "created_at": _ts(2, 9, 10),
    },
    # case-005 — 1 signal
    {
        "id": 10, "case_id": "case-005", "source": "Aduan Wali Murid",
        "source_confidence": 0.63, "urgency": "Sedang", "status": "Sedang Ditinjau",
        "summary": "Buah dan susu tidak tersedia beberapa hari di SDN Condongcatur 02",
        "text": "Wali murid melaporkan buah dan susu tidak tersedia pada beberapa hari distribusi.",
        "created_at": _ts(2, 9, 5),
    },
    # case-006 — 1 signal
    {
        "id": 11, "case_id": "case-006", "source": "Hotline Sekolah",
        "source_confidence": 0.59, "urgency": "Sedang", "status": "Sedang Ditinjau",
        "summary": "Makanan diterima dalam kondisi dingin dan sedikit terlambat di SDN Medan Johor 09",
        "text": "Aduan makanan dingin dan keterlambatan ringan; tampak isu operasional rute.",
        "created_at": _ts(3, 8, 10),
    },
    # case-007 — 2 signal
    {
        "id": 12, "case_id": "case-007", "source": "Laporan Pengawas",
        "source_confidence": 0.71, "urgency": "Tinggi", "status": "Terhubung ke Kasus",
        "summary": "Menu aktual tidak sesuai rencana di SMPN 35 Surabaya",
        "text": "Pengawas mencatat menu aktual berulang kali tidak sesuai dengan rencana menu.",
        "created_at": _ts(2, 7, 30),
    },
    {
        "id": 13, "case_id": "case-007", "source": "Laporan Harian Vendor",
        "source_confidence": 0.55, "urgency": "Sedang", "status": "Sedang Ditinjau",
        "summary": "Foto laporan harian terindikasi mirip dengan hari sebelumnya",
        "text": "Sistem menandai indikasi kemiripan foto antar hari; perlu peninjauan operator.",
        "created_at": _ts(3, 10, 0),
    },
    # case-008 — 1 signal
    {
        "id": 14, "case_id": "case-008", "source": "Laporan Komunitas",
        "source_confidence": 0.68, "urgency": "Tinggi", "status": "Terhubung ke Kasus",
        "summary": "Kekhawatiran higiene area dapur di SMPN 12 Bandung",
        "text": "Laporan komunitas menyebut kondisi higiene dapur perlu diperiksa.",
        "created_at": _ts(3, 7, 45),
    },
    # case-009 — 1 signal
    {
        "id": 15, "case_id": "case-009", "source": "Operator Sekolah",
        "source_confidence": 0.50, "urgency": "Rendah", "status": "Terhubung ke Kasus",
        "summary": "Checklist distribusi belum lengkap di SDN Tembalang 01",
        "text": "Operator sekolah melaporkan checklist distribusi belum sepenuhnya terisi.",
        "created_at": _ts(1, 8, 0),
    },
    # case-010 — 1 signal
    {
        "id": 16, "case_id": "case-010", "source": "Aduan Wali Murid",
        "source_confidence": 0.48, "urgency": "Rendah", "status": "Terhubung ke Kasus",
        "summary": "Keterlambatan distribusi terisolasi di SDN Renon 04",
        "text": "Satu laporan keterlambatan distribusi; tidak berulang.",
        "created_at": _ts(1, 9, 0),
    },
    # Signal yang BELUM dibentuk kasus (case_id=None) — intake murni
    {
        "id": 17, "case_id": None, "source": "Media Sosial",
        "source_confidence": 0.41, "urgency": "Rendah", "status": "Belum Dibentuk Kasus",
        "summary": "Unggahan warganet menyebut porsi kecil di sebuah sekolah (lokasi belum jelas)",
        "text": "Sinyal publik belum tervalidasi; lokasi dan vendor belum dapat dipastikan.",
        "vendor_id": None, "vendor_name": "Belum teridentifikasi",
        "region": "Belum teridentifikasi", "school": "Belum teridentifikasi",
        "created_at": _ts(4, 7, 20),
    },
    {
        "id": 18, "case_id": None, "source": "Formulir Publik",
        "source_confidence": 0.44, "urgency": "Sedang", "status": "Belum Dibentuk Kasus",
        "summary": "Aduan rasa makanan kurang enak, tanpa detail vendor/sekolah",
        "text": "Sinyal publik masuk tanpa detail vendor atau sekolah; perlu triase operator.",
        "vendor_id": None, "vendor_name": "Belum teridentifikasi",
        "region": "Belum teridentifikasi", "school": "Belum teridentifikasi",
        "created_at": _ts(4, 6, 50),
    },
    # ── Skenario evidence fusion: kontaminasi belatung (Lampung) ──────────
    # Laporan resmi utama (siap ditinjau untuk pembentukan kasus). Lampiran 4.jpg.
    {
        "id": 19, "case_id": None, "source": "Laporan Pengawas",
        "source_confidence": 0.86, "urgency": "Kritis", "status": "Belum Dibentuk Kasus",
        "summary": "Laporan pengawas: dugaan kontaminasi belatung pada makanan MBG di SDN 1 Karang Agung",
        "text": ("Laporan resmi pengawas menyebut dugaan kontaminasi belatung pada makanan MBG. "
                 "Lokasi spesifik teridentifikasi dan disertai lampiran foto."),
        "vendor_id": None, "vendor_name": "Belum teridentifikasi",
        "region": "Lampung", "district": "Kabupaten Tanggamus", "school": "SDN 1 Karang Agung",
        "issue_category": "dugaan keamanan pangan",
        "attachment_path": f"{EVIDENCE_MEDIA_BASE}/4.jpg",
        "attachment_title": "Foto laporan resmi dugaan kontaminasi belatung",
        "attachment_source": "Laporan Resmi",
        "attachment_note": ("Foto laporan resmi menunjukkan indikasi yang memerlukan verifikasi sanitasi dan "
                            "pemeriksaan lapangan segera. Foto tidak menjadi keputusan final atau penetapan pelanggaran."),
        "created_at": _ts(4, 9, 10),
    },
    # Signal media sosial pendukung. Lampiran 26.jpg. Lokasi hanya provinsi.
    {
        "id": 20, "case_id": None, "source": "Media Sosial",
        "source_confidence": 0.38, "urgency": "Sedang", "status": "Belum Dibentuk Kasus",
        "summary": "Unggahan media sosial menyebut dugaan belatung pada MBG anak SD di Lampung",
        "text": "di lampung ada belatung di mbg anak sd",
        "vendor_id": None, "vendor_name": "Belum teridentifikasi",
        "region": "Lampung", "district": "Belum teridentifikasi", "school": "Belum teridentifikasi",
        "issue_category": "dugaan keamanan pangan",
        "attachment_path": f"{EVIDENCE_MEDIA_BASE}/26.jpg",
        "attachment_title": "Lampiran unggahan media sosial terkait dugaan keamanan pangan",
        "attachment_source": "Media Sosial",
        "attachment_note": ("Sinyal pendukung dari wilayah Lampung; hubungan dengan SDN 1 Karang Agung belum "
                            "terkonfirmasi dan memerlukan verifikasi operator."),
        "created_at": _ts(4, 11, 40),
    },
]


def _enrich_signal(sig: dict[str, Any]) -> dict[str, Any]:
    """Isi vendor/region/school dari kasus bila signal terhubung."""
    out = dict(sig)
    if sig.get("case_id"):
        case = CASE_BY_ID[sig["case_id"]]
        vendor = VENDOR_BY_ID[case["vendor_id"]]
        out.setdefault("vendor_id", vendor["id"])
        out.setdefault("vendor_name", vendor["name"])
        out.setdefault("region", vendor["region"])
        out.setdefault("district", vendor["district"])
        out.setdefault("school", case["school"])
        out.setdefault("issue_category", case["issue_category"])
    else:
        out.setdefault("district", "Belum teridentifikasi")
        out.setdefault("issue_category", "belum diklasifikasi")
    return out


SIGNALS = [_enrich_signal(s) for s in SIGNALS]


# ── Bukti (evidence) — 2–3 per kasus, dipetakan ke foto ──────────────────
# Peta kasus -> daftar nomor foto.
_CASE_PHOTOS: dict[str, list[int]] = {
    "case-001": [1, 2, 3],
    # 4.jpg direalokasi sebagai bukti utama skenario kontaminasi belatung
    # (lihat SCENARIO_SIGNALS). case-002 tetap 2 bukti.
    "case-002": [5, 6],
    "case-003": [7, 8, 9],
    "case-004": [10, 11],
    "case-005": [12, 13, 14],
    "case-006": [15, 16],
    "case-007": [17, 18, 19],
    "case-008": [20, 21],
    "case-009": [22, 23],
    "case-010": [24, 25],
}

# Template bukti per kasus: (tipe, judul, catatan operator, status_review).
# confidence_score adalah indikator pra-verifikasi, bukan klaim gizi pasti.
_EVIDENCE_TEMPLATE = [
    ("photo", "Foto porsi makan siang", "indikasi awal, perlu perbandingan dengan menu dan standar porsi", "Perlu Ditinjau"),
    ("document", "Laporan harian & menu (simulasi OCR)", "OCR menu terbaca sebagian; total biaya perlu konfirmasi operator", "Perlu Ditinjau"),
    ("metadata", "Metadata waktu distribusi", "catatan waktu distribusi vs jadwal; perlu validasi lapangan", "Perlu Ditinjau"),
]


def _build_evidence() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    eid = 1
    for case in CASES:
        cid = case["case_id"]
        vendor = VENDOR_BY_ID[case["vendor_id"]]
        photos = _CASE_PHOTOS[cid]
        # Signal asal bila ada.
        case_signals = [s["id"] for s in SIGNALS if s.get("case_id") == cid]
        for i, photo_n in enumerate(photos):
            tpl = _EVIDENCE_TEMPLATE[i % len(_EVIDENCE_TEMPLATE)]
            ev_type, base_title, note, review = tpl
            confidence = round(0.58 + (i * 0.06), 2)
            items.append({
                "id": eid,
                "case_id": cid,
                "signal_id": case_signals[i] if i < len(case_signals) else (case_signals[0] if case_signals else None),
                "type": ev_type,
                "title": f"{base_title} — {case['school']}",
                "file_path": f"{EVIDENCE_MEDIA_BASE}/{photo_n}.jpg",
                "linked_entity": case_number(cid),
                "source": "Laporan harian vendor" if ev_type != "photo" else "Distribusi lapangan",
                "ocr_result": ("Simulasi OCR: menu terbaca 'nasi, telur, sayur' dengan keyakinan sedang."
                               if ev_type == "document" else None),
                "image_text_match_score": round(0.44 + (i * 0.05), 2) if ev_type == "photo" else None,
                "duplicate_score": round(0.18 + (i * 0.14), 2) if ev_type == "photo" else None,
                "confidence_score": confidence,
                "review_status": review,
                "reviewer_note": f"Foto {ev_type} untuk {vendor['name']}: {note}.",
                "created_at": case["created_at"],
            })
            eid += 1
    return items


EVIDENCE = _build_evidence()

# Golden path: pertegas catatan bukti case-001 sesuai spesifikasi.
for _ev in EVIDENCE:
    if _ev["case_id"] == "case-001" and _ev["type"] == "photo":
        _ev["reviewer_note"] = (
            "Foto porsi makan siang — indikasi awal, perlu perbandingan dengan menu dan "
            "standar porsi. Bukan bukti pelanggaran; wajib ditinjau operator."
        )
        break


# ── Penilaian Risiko (satu per kasus) ────────────────────────────────────
_PRIORITY_TO_SCORE = {"Kritis": 88, "Tinggi": 78, "Sedang": 58, "Rendah": 38}


# Skor gizi demo per kasus (simulasi penilaian foto MBG; null = belum dinilai).
_NUTRITION_DEMO: dict[str, int | None] = {
    "case-001": 58,   # keluhan porsi/protein
    "case-002": 42,   # higiene / keracunan
    "case-003": 71,
    "case-004": 55,   # anomali biaya + menu
    "case-005": 68,
    "case-006": 74,
    "case-007": 61,
    "case-008": 38,   # higiene
    "case-009": 82,
    "case-010": 77,
}


def _build_risk() -> list[dict[str, Any]]:
    """Satu record risiko per kasus — severity, keyakinan, actionability (+ gizi demo)."""
    out: list[dict[str, Any]] = []
    for idx, case in enumerate(CASES, start=1):
        vendor = VENDOR_BY_ID[case["vendor_id"]]
        label = case["priority_label"]
        if case["case_id"] == "case-001":
            severity, trust, actionability = 90, 82, 84
            final = min(95, int(severity * 0.50 + trust * 0.25 + actionability * 0.25))
            out.append({
                "id": idx, "case_id": case["case_id"], "vendor_id": vendor["id"],
                "vendor_name": vendor["name"], "region": vendor["region"],
                "severity_score": severity, "confidence_score": trust,
                "actionability_score": actionability,
                "nutrition_score": _NUTRITION_DEMO.get(case["case_id"]),
                "final_priority_score": final, "priority_label": "Tinggi",
                "explanation": (
                    "Prioritas tinggi karena aduan berulang, pola keterlambatan distribusi, "
                    "estimasi protein rendah, dan ketidaksesuaian laporan harian saling menguatkan. "
                    "Severity 90, keyakinan 82, actionability 84, gizi 58/100 (estimasi dari bukti foto). "
                    "Peninjauan operator tetap diperlukan karena kecocokan gambar-teks parsial."
                ),
                "recommended_action": vendor["recommended_action"],
                "computed_at": _ts(4, 13, 5),
                "ai_notice": GOVERNANCE_NOTICE,
            })
            continue
        base = _PRIORITY_TO_SCORE[label]
        severity = base
        trust = max(45, 82 - idx * 3)
        actionability = 30 + (idx * 11) % 55
        final = min(95, int(severity * 0.50 + trust * 0.25 + actionability * 0.25))
        out.append({
            "id": idx, "case_id": case["case_id"], "vendor_id": vendor["id"],
            "vendor_name": vendor["name"], "region": vendor["region"],
            "severity_score": severity, "confidence_score": trust,
            "actionability_score": actionability,
            "nutrition_score": _NUTRITION_DEMO.get(case["case_id"]),
            "final_priority_score": final, "priority_label": label,
            "explanation": (
                f"Prioritas {label.lower()} — severity {severity}/100, keyakinan {trust}/100, "
                f"actionability {actionability}/100"
                + (
                    f", gizi {_NUTRITION_DEMO[case['case_id']]}/100 (estimasi dari bukti foto)."
                    if _NUTRITION_DEMO.get(case["case_id"]) is not None
                    else "."
                )
                + " Validasi operator diperlukan sebelum eskalasi."
            ),
            "recommended_action": vendor["recommended_action"],
            "computed_at": _ts(4, 13, idx),
            "ai_notice": GOVERNANCE_NOTICE,
        })
    return out


RISK = _build_risk()
RISK_BY_CASE = {r["case_id"]: r for r in RISK}


# ── Tiket (satu aktif per kasus yang butuh tindakan) ─────────────────────
# Status board: Baru, Sedang Ditinjau, Menunggu Klarifikasi Vendor,
# Verifikasi Lapangan, Selesai.
#
# SLA sengaja TIDAK didaftarkan di sini: nilainya diturunkan dari keparahan
# kasus lewat ``app.ticketing`` supaya seed tidak lagi bisa memasangkan kasus
# Kritis dengan SLA 72h. Kolom di bawah hanya berisi data operasional yang
# memang khas per kasus.
_CASE_TICKET = {
    "case-001": ("Baru", "Dinas Kesehatan Jakarta Timur", "Rina Kartika", "Verifikasi Lapangan"),
    "case-002": ("Verifikasi Lapangan", "Dinas Kesehatan Kota Bandung", "Andi Prasetyo", "Verifikasi Lapangan"),
    "case-003": ("Menunggu Klarifikasi Vendor", "Meja Tinjauan Pengadaan", "Siti Rahayu", "Klarifikasi menu & biaya"),
    "case-004": ("Menunggu Klarifikasi Vendor", "Unit Pengawasan Vendor MBG", "Budi Santoso", "Perbaikan faktur & dokumen"),
    "case-005": ("Sedang Ditinjau", "Tim Kepatuhan Gizi", "Maya Lestari", "Konfirmasi substitusi menu"),
    "case-006": ("Sedang Ditinjau", "Unit Pengawasan Vendor MBG", None, "Pantau rute distribusi"),
    "case-007": ("Menunggu Klarifikasi Vendor", "Tim Kepatuhan Gizi", "Maya Lestari", "Verifikasi menu aktual"),
    "case-008": ("Verifikasi Lapangan", "Dinas Kesehatan Kota Bandung", "Andi Prasetyo", "Inspeksi higiene dapur"),
    "case-009": ("Selesai", "Unit Pengawasan Vendor MBG", "Budi Santoso", "Checklist telah dilengkapi"),
    "case-010": ("Selesai", "Unit Pengawasan Vendor MBG", "Budi Santoso", "Isu operasional teratasi"),
}

_IMPACT_BY_ISSUE = {
    "indikasi keracunan makanan": "Luas",
    "porsi protein kurang": "Sedang",
    "anomali biaya": "Sedang",
}


def _build_tickets() -> list[dict[str, Any]]:
    from app import ticketing  # local import: ticketing has no seed_data dependency

    out: list[dict[str, Any]] = []
    for idx, case in enumerate(CASES, start=1):
        cid = case["case_id"]
        vendor = VENDOR_BY_ID[case["vendor_id"]]
        risk = RISK_BY_CASE[cid]
        status, unit, assignee, action = _CASE_TICKET[cid]
        ev_ids = [e["id"] for e in EVIDENCE if e["case_id"] == cid]
        # Severity inherited from the case; SLA derived from it.
        severity = case.get("severity") or case["priority_label"]
        impact = _IMPACT_BY_ISSUE.get(case["issue_category"], ticketing.DEFAULT_IMPACT)
        urgency = "Segera" if severity == "Kritis" else ticketing.DEFAULT_URGENCY
        policy = ticketing.policy_for(severity, impact, urgency)
        resolved = status in ticketing.TERMINAL_STATUSES
        out.append({
            "id": f"tkt-{idx:03d}",
            "case_id": cid,
            "title": f"Tinjauan {case['priority_label'].lower()}: {vendor['name']}",
            "description": f"Tindak lanjut {case['issue_category']} pada {case['school']}.",
            "status": status,
            "severity": severity,
            "impact": impact,
            "urgency": urgency,
            "sla_policy": policy,
            "sla": ticketing.sla_label(policy),
            "due_at": ticketing.due_at(case["created_at"], policy),
            "resolved_at": case["updated_at"] if resolved else None,
            "assignee": assignee,
            "assignment_group": unit,
            "assigned_unit": unit,
            "escalation_level": severity,
            "linked_vendor_id": vendor["id"],
            "linked_vendor_name": vendor["name"],
            "linked_region": vendor["region"],
            "priority": risk["final_priority_score"],
            "category": case["issue_category"],
            "labels": [],
            "notes": [],
            "recommended_action": action if cid != "case-001" else "Jadwalkan verifikasi lapangan dan minta klarifikasi vendor.",
            "linked_evidence_ids": ev_ids,
            "audit_preview": "Tiket dibuat dari peninjauan bukti dan diantrekan untuk tinjauan manusia.",
            "workstream": "Tindak lanjut",
            "created_at": case["created_at"],
            "updated_at": case["updated_at"],
        })
    return out


TICKETS = [t for t in _build_tickets()]
TICKET_BY_CASE = {t["case_id"]: t for t in TICKETS}


# ── Jejak Audit ──────────────────────────────────────────────────────────
def _build_audit() -> list[dict[str, Any]]:
    """Kronologi formal per kasus: signal → kasus → bukti → risiko → tiket."""
    out: list[dict[str, Any]] = []
    aid = 1
    for case in CASES:
        cid = case["case_id"]
        ticket = TICKET_BY_CASE[cid]
        base_day = int("".join(ch for ch in case["created_at"][8:10]))
        steps = [
            ("signal_received", "Sistem Intake", "Sistem", "Signal intake diterima dan dikelompokkan.", base_day, 8),
            ("case_formed", "Operator Dewi", "Operator Distrik", f"Kasus {case_number(cid)} dibentuk dari sinyal terhubung.", base_day, 9),
            ("evidence_reviewed", "Operator Dewi", "Operator Distrik", "Bukti ditinjau sebagai sinyal pra-verifikasi.", base_day + 1, 10),
            ("risk_computed", "Layanan Penilaian", "Sistem", f"Penilaian risiko dihitung: {RISK_BY_CASE[cid]['priority_label']}.", base_day + 1, 11),
            ("ticket_created", "Operator Dewi", "Operator Distrik", f"Tiket {ticket['id']} dibuat untuk tindak lanjut.", base_day + 2, 12),
        ]
        for ev_type, actor, role, desc, day, hour in steps:
            out.append({
                "id": aid, "case_id": cid, "ticket_id": ticket["id"],
                "event_type": ev_type, "actor": actor, "role": role,
                "description": desc, "timestamp": _ts(min(day, 4), hour, aid % 60),
            })
            aid += 1
        if ticket["status"] == "Selesai":
            out.append({
                "id": aid, "case_id": cid, "ticket_id": ticket["id"],
                "event_type": "status_changed", "actor": "Supervisor Bima", "role": "Supervisor",
                "description": "Kasus ditandai selesai setelah tindak lanjut operator.",
                "timestamp": case["updated_at"],
            })
            aid += 1
    return out


AUDIT = _build_audit()


# ── Agregat turunan (heatmap, tren, anomali, overview) ───────────────────
REGIONAL_HEATMAP = [
    {
        "region": v["region"], "district": v["district"], "risk_score": v["risk_score"],
        "complaint_count": len([s for s in SIGNALS if s.get("vendor_id") == v["id"]]),
        "high_priority_cases": len([c for c in CASES if c["vendor_id"] == v["id"]
                                    and RISK_BY_CASE[c["case_id"]]["final_priority_score"] >= 65]),
        "latitude": _LATLNG[i][0], "longitude": _LATLNG[i][1],
    }
    for i, v in enumerate(VENDORS)
]

TRENDS = [
    {"date": f"2026-05-{25 + i:02d}", "complaints": 12 + i * 3, "high_priority": 2 + i % 4, "avg_score": 52 + i * 4}
    for i in range(8)
]

ANOMALIES = [
    {"id": "ano-001", "region": "DKI Jakarta", "issue_category": "porsi protein kurang",
     "description": "Volume aduan naik 2,8x dibanding rata-rata tujuh hari.", "severity": "Tinggi", "linked_vendor_id": "vnd-001"},
    {"id": "ano-002", "region": "Jawa Barat", "issue_category": "indikasi keracunan makanan",
     "description": "Dua sekolah melaporkan gejala serupa dalam 48 jam.", "severity": "Kritis", "linked_vendor_id": "vnd-002"},
    {"id": "ano-003", "region": "Jawa Timur", "issue_category": "anomali biaya",
     "description": "Biaya per porsi melampaui patokan sementara kelengkapan menu menurun.", "severity": "Tinggi", "linked_vendor_id": "vnd-004"},
]
