// Pemetaan kasus internal -> tampilan publik "Lacak Laporan".
// Halaman /lacak/[id] hanya boleh membaca dari sini: apa pun yang tidak
// dipetakan di file ini tidak pernah sampai ke pelapor.

import type { AuditTrailEvent, OversightCase } from "@/types/monitoring";

/** Tahap perjalanan laporan versi warga (bukan status internal). */
export const STAGES = ["Diterima", "Diverifikasi", "Diproses", "Ditindaklanjuti", "Selesai"] as const;
export type Stage = (typeof STAGES)[number];

/** Kondisi tampilan halaman lacak. */
export type TrackState = "in_progress" | "completed" | "closed" | "waiting_info";

interface StatusView {
  /** Tahap terakhir yang sudah dilewati (indeks ke STAGES). */
  stageIndex: number;
  state: TrackState;
  /** Label status ramah warga yang tampil di badge utama. */
  label: string;
  /** Penjelasan satu kalimat tentang arti status ini. */
  meaning: string;
  /** Langkah berikutnya yang diharapkan; null bila laporan sudah tuntas. */
  nextStep: string | null;
}

// Kunci = status internal kasus (lihat CASE_STATUSES di halaman operator).
const STATUS_VIEW: Record<string, StatusView> = {
  "Open & Monitored": {
    stageIndex: 0,
    state: "in_progress",
    label: "Laporan Diterima",
    meaning: "Laporan Anda sudah masuk dan sedang menunggu antrean pemeriksaan awal.",
    nextStep: "Petugas akan memeriksa kelengkapan dan kecocokan laporan Anda.",
  },
  Assessing: {
    stageIndex: 1,
    state: "in_progress",
    label: "Sedang Diverifikasi",
    meaning: "Petugas sedang memeriksa isi laporan dan bukti yang Anda kirimkan.",
    nextStep: "Setelah verifikasi selesai, laporan diteruskan ke unit penanganan.",
  },
  "In Handling": {
    stageIndex: 2,
    state: "in_progress",
    label: "Sedang Diproses",
    meaning: "Laporan Anda sedang ditangani oleh unit yang berwenang.",
    nextStep: "Unit penanganan akan melakukan tindak lanjut di lapangan atau ke penyedia.",
  },
  Escalated: {
    stageIndex: 3,
    state: "in_progress",
    label: "Ditindaklanjuti",
    meaning: "Laporan Anda dinaikkan ke tingkat penanganan yang lebih tinggi karena dinilai mendesak.",
    nextStep: "Hasil tindak lanjut akan diverifikasi sebelum laporan dinyatakan selesai.",
  },
  "Pending / Blocked": {
    stageIndex: 2,
    state: "waiting_info",
    label: "Menunggu Informasi Tambahan",
    meaning: "Penanganan tertahan karena masih ada keterangan atau data yang perlu dilengkapi.",
    nextStep: "Anda dapat membantu mempercepat proses dengan menambahkan informasi.",
  },
  "Resolved – Pending Verification": {
    stageIndex: 3,
    state: "in_progress",
    label: "Menunggu Verifikasi Akhir",
    meaning: "Tindak lanjut sudah dilakukan dan hasilnya sedang diperiksa ulang.",
    nextStep: "Bila hasil verifikasi sesuai, laporan akan dinyatakan selesai.",
  },
  Closed: {
    stageIndex: 4,
    state: "completed",
    label: "Selesai",
    meaning: "Penanganan laporan Anda telah selesai dan diverifikasi.",
    nextStep: null,
  },
  Reopened: {
    stageIndex: 2,
    state: "in_progress",
    label: "Dibuka Kembali",
    meaning: "Laporan dibuka kembali karena masalah dinilai belum sepenuhnya tuntas.",
    nextStep: "Unit penanganan akan meninjau ulang dan melanjutkan tindak lanjut.",
  },
  "Merged / Invalid": {
    stageIndex: 4,
    state: "closed",
    label: "Ditutup",
    meaning:
      "Laporan ini ditutup karena digabungkan dengan laporan lain yang serupa atau tidak dapat ditindaklanjuti.",
    nextStep: null,
  },
};

const DEFAULT_VIEW: StatusView = {
  stageIndex: 0,
  state: "in_progress",
  label: "Laporan Diterima",
  meaning: "Laporan Anda sudah tercatat dan sedang dalam antrean penanganan.",
  nextStep: "Petugas akan memeriksa laporan Anda.",
};

export function statusView(status: string): StatusView {
  return STATUS_VIEW[status] ?? DEFAULT_VIEW;
}

// Hanya peristiwa di daftar ini yang boleh tampil ke publik. Peristiwa lain
// (mis. pelepasan sinyal, pembaruan kepemilikan, catatan internal) sengaja
// tidak dipetakan sehingga otomatis tersaring.
const PUBLIC_EVENTS: Record<string, { label: string; text: string }> = {
  signal_received: { label: "Diterima", text: "Laporan Anda diterima dan tercatat dalam sistem." },
  case_formed: { label: "Diverifikasi", text: "Laporan lolos pemeriksaan awal dan dibuatkan berkas penanganan." },
  evidence_reviewed: { label: "Diverifikasi", text: "Bukti yang Anda lampirkan selesai diperiksa petugas." },
  risk_computed: { label: "Diproses", text: "Laporan selesai dinilai tingkat prioritasnya untuk penjadwalan tindak lanjut." },
  ticket_created: { label: "Ditindaklanjuti", text: "Tindak lanjut resmi dibuka dan diteruskan ke unit penanganan." },
  status_changed: { label: "Diproses", text: "Status penanganan laporan Anda diperbarui." },
  handling_update: { label: "Diproses", text: "Ada kemajuan baru pada penanganan laporan Anda." },
};

export interface PublicEvent {
  id: number;
  label: string;
  text: string;
  timestamp: string;
  /** Unit penanggung jawab, digeneralisasi — bukan nama petugas. */
  unit: string;
}

/**
 * Jejak aktivitas versi publik: hanya jenis peristiwa yang aman, tanpa
 * deskripsi internal dan tanpa identitas petugas (peran saja).
 */
export function publicTimeline(events: AuditTrailEvent[]): PublicEvent[] {
  return events
    .filter((event) => event.event_type in PUBLIC_EVENTS)
    .map((event) => ({
      id: event.id,
      ...PUBLIC_EVENTS[event.event_type],
      timestamp: event.timestamp,
      unit: genericUnit(event.role),
    }))
    .sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp));
}

/** Nama orang tidak pernah ditampilkan; peran diringkas jadi unit generik. */
function genericUnit(role: string | null | undefined): string {
  const value = (role ?? "").toLowerCase();
  if (value.includes("sistem") || value.includes("system") || value.includes("otomat")) return "Sistem MonitorMBG";
  if (value.includes("verif") || value.includes("lapangan")) return "Tim Verifikasi Lapangan";
  if (value.includes("vendor") || value.includes("penyedia")) return "Unit Pengawasan Penyedia";
  return "Petugas Pengawasan MBG";
}

/** Lokasi umum saja — sekolah/alamat persis tidak ditampilkan ke publik. */
export function generalLocation(item: OversightCase): string {
  const parts = [item.district, item.region].filter((part) => part && part !== "Belum teridentifikasi");
  return parts.length ? parts.join(", ") : "Belum teridentifikasi";
}

/** Kanal masuk laporan, dibaca dari sinyal pertama yang terhubung. */
export function submissionChannel(item: OversightCase): string {
  const origin = item.signals[0]?.intake_origin ?? "";
  if (origin === "public_form") return "Formulir Lapor MBG";
  if (origin.startsWith("scraper")) return "Pemantauan kanal publik";
  return item.signals[0]?.source ?? "Formulir Lapor MBG";
}

export function formatDateTime(value: string): string {
  return new Date(value).toLocaleString("id-ID", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** "3 hari lalu" — jarak waktu dalam bahasa sehari-hari. */
export function relativeTime(value: string): string {
  const days = Math.floor((Date.now() - Date.parse(value)) / 86_400_000);
  if (days <= 0) return "hari ini";
  if (days === 1) return "kemarin";
  if (days < 30) return `${days} hari lalu`;
  const months = Math.floor(days / 30);
  return months < 12 ? `${months} bulan lalu` : `${Math.floor(months / 12)} tahun lalu`;
}
