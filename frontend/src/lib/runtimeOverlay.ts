// Overlay runtime operator (durable lintas refresh via localStorage).
//
// AKAR MASALAH yang diperbaiki: aplikasi punya dua sumber data — runtime
// in-memory backend dan store fallback frontend — tanpa flag mode global.
// Tiap halaman membaca API lebih dulu, sehingga mutasi operator (merge signal,
// evidence baru, kasus baru, unlink) HILANG saat backend restart / halaman
// di-refresh, karena API mengembalikan data seed lagi.
//
// Solusi: catat SETIAP mutasi operator ke localStorage lalu OVERLAY di atas
// apa pun yang dikembalikan API/fallback. Dengan begitu Kotak Masuk Sinyal,
// Detail Kasus, dan Jejak Audit selalu menampilkan hasil fusion yang konsisten,
// baik API hidup maupun mati, dan tetap bertahan setelah refresh.
//
// Overlay TIDAK menghapus aset fisik atau audit lama; unlink hanya menandai
// relasi berakhir dan menambah audit event.

import type { AuditTrailEvent, Evidence, OversightCase, Signal } from "@/types/monitoring";
import { normalizeCase } from "@/lib/scoreDisplay";

const KEY = "mbg.runtimeOverlay.v1";

interface SignalLink {
  case_id: string | null;
  case_number: string | null;
  status: string;
  issue_category?: string;
}

interface OverlayState {
  // Perubahan relasi signal (link saat merge/create, atau lepas saat unlink).
  signalLinks: Record<number, SignalLink>;
  // Kasus hasil runtime (create) atau snapshot terbaru kasus yang dimerge.
  cases: Record<string, OversightCase>;
  // Evidence yang dilepas dari kasus (id -> true).
  unlinkedEvidence: Record<number, boolean>;
  // Audit event tambahan (create/merge/unlink/dst).
  audit: AuditTrailEvent[];
}

function empty(): OverlayState {
  return { signalLinks: {}, cases: {}, unlinkedEvidence: {}, audit: [] };
}

function read(): OverlayState {
  if (typeof window === "undefined") return empty();
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return empty();
    return { ...empty(), ...(JSON.parse(raw) as OverlayState) };
  } catch {
    return empty();
  }
}

function write(state: OverlayState): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    // Kuota penuh / storage dimatikan: overlay tetap berlaku untuk sesi ini
    // via memori pemanggil; kita tidak menggagalkan aksi.
  }
}

// ── Pencatatan mutasi ────────────────────────────────────────────────────

/** Simpan/segarkan snapshot kasus (create atau hasil merge) + relasi sinyalnya. */
export function recordCase(caseData: OversightCase): void {
  const state = read();
  const normalized = normalizeCase(caseData);
  state.cases[normalized.case_id] = normalized;
  for (const sig of normalized.signals ?? []) {
    state.signalLinks[sig.id] = {
      case_id: caseData.case_id,
      case_number: caseData.case_number ?? null,
      status: "Terhubung ke Kasus",
      issue_category: caseData.issue_category,
    };
  }
  mergeAudit(state, caseData.audit_events ?? []);
  write(state);
}

/** Catat tautan satu sinyal ke kasus (dipakai bila hanya signal yang berubah). */
export function recordSignalLink(signalId: number, link: SignalLink): void {
  const state = read();
  state.signalLinks[signalId] = link;
  write(state);
}

/** Catat pelepasan sinyal dari kasus; sinyal kembali perlu ditinjau. */
export function recordUnlink(
  signalId: number,
  caseId: string,
  evidenceIds: number[],
  auditEvents: AuditTrailEvent[],
  updatedCase?: OversightCase,
): void {
  const state = read();
  state.signalLinks[signalId] = { case_id: null, case_number: null, status: "Perlu Ditinjau" };
  for (const id of evidenceIds) state.unlinkedEvidence[id] = true;
  if (updatedCase) state.cases[caseId] = updatedCase;
  mergeAudit(state, auditEvents);
  write(state);
}

/** Tambahkan audit event runtime (mis. dari respons merge API). */
export function recordAudit(events: AuditTrailEvent[]): void {
  const state = read();
  mergeAudit(state, events);
  write(state);
}

function mergeAudit(state: OverlayState, events: AuditTrailEvent[]): void {
  for (const ev of events) {
    if (!state.audit.some((e) => e.id === ev.id)) state.audit.push(ev);
  }
}

// ── Penerapan overlay pada data API/fallback ─────────────────────────────

/** Overlay relasi sinyal pada daftar sinyal apa pun (API atau fallback). */
export function applySignals(signals: Signal[]): Signal[] {
  const state = read();
  return signals.map((sig) => {
    const link = state.signalLinks[sig.id];
    if (!link) return sig;
    return { ...sig, case_id: link.case_id, status: link.status, issue_category: link.issue_category ?? sig.issue_category };
  });
}

/** Kasus runtime yang belum tentu dikembalikan API (mis. dibuat offline). */
export function overlayCases(): OversightCase[] {
  return Object.values(read().cases);
}

/** Ambil snapshot kasus runtime bila ada (dipakai halaman detail). */
export function getOverlayCase(caseId: string): OversightCase | null {
  const raw = read().cases[caseId];
  return raw ? normalizeCase(raw) : null;
}

/**
 * Rekonsiliasi kasus dari API dengan overlay runtime. Bila overlay lebih baru
 * (mis. sudah ada evidence hasil merge yang belum diketahui API karena restart),
 * pakai snapshot overlay. Evidence yang dilepas ditandai.
 */
export function reconcileCase(apiCase: OversightCase | null, caseId: string): OversightCase | null {
  const overlay = getOverlayCase(caseId);
  const base = pickFreshest(apiCase, overlay);
  if (!base) return null;
  return markUnlinkedEvidence(base);
}

function pickFreshest(a: OversightCase | null, b: OversightCase | null): OversightCase | null {
  if (!a) return b;
  if (!b) return a;
  // Snapshot dengan evidence terbanyak = paling lengkap pasca-fusion; bila sama,
  // pakai updated_at terbaru.
  if ((b.evidence?.length ?? 0) !== (a.evidence?.length ?? 0)) {
    return (b.evidence?.length ?? 0) > (a.evidence?.length ?? 0) ? b : a;
  }
  return Date.parse(b.updated_at) >= Date.parse(a.updated_at) ? b : a;
}

function markUnlinkedEvidence(caseData: OversightCase): OversightCase {
  const state = read();
  if (Object.keys(state.unlinkedEvidence).length === 0) return caseData;
  const evidence = (caseData.evidence ?? []).map((e: Evidence) =>
    state.unlinkedEvidence[e.id] ? { ...e, unlinked_from_case: true, review_status: "Dilepas dari kasus" } : e,
  );
  return { ...caseData, evidence };
}

/** Gabungkan audit event runtime dengan daftar audit dari API/fallback. */
export function applyAudit(events: AuditTrailEvent[]): AuditTrailEvent[] {
  const state = read();
  const byId = new Map(events.map((e) => [e.id, e]));
  for (const ev of state.audit) byId.set(ev.id, ev);
  return [...byId.values()];
}

/** Reset overlay (utilitas demo/test). */
export function clearOverlay(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* abaikan */
  }
}
