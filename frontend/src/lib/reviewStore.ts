// Runtime demo store (offline) untuk workflow "Tinjau & Bentuk Kasus".
// Dipakai HANYA bila backend tidak tersedia. Memutasi array fallback yang
// diimpor (singleton modul, hidup selama sesi) sehingga kasus baru / tautan
// sinyal / audit langsung terlihat di Kotak Masuk Sinyal, Detail Kasus, dan
// Jejak Audit dalam sesi yang sama. Tidak mengubah seed asli secara destruktif
// (mutasi hanya pada salinan runtime di memori browser).

import {
  fallbackAudit,
  fallbackCases,
  fallbackEvidence,
  fallbackInvestigators,
  fallbackLocationRegistry,
  fallbackSignals,
  fallbackUnits,
  fallbackVendors,
} from "@/lib/demoFallback";
import { caseNumber } from "@/lib/utils";
import type {
  AuditTrailEvent,
  AssignmentCandidate,
  AssignmentOptions,
  LocationRegistryEntry,
  OversightCase,
  ScoreResult,
  Signal,
  Vendor,
} from "@/types/monitoring";

const GOVERNANCE =
  "Data dan analisis pada halaman ini merupakan sinyal pra-verifikasi untuk membantu prioritisasi. Verifikasi lapangan dan keputusan akhir tetap dilakukan oleh operator berwenang.";

const UNKNOWN_VENDOR: Vendor = {
  id: "vnd-unknown",
  name: "Belum teridentifikasi",
  region: "Belum teridentifikasi",
  district: "Belum teridentifikasi",
  assigned_schools: ["Belum teridentifikasi"],
  daily_meal_volume: 0,
  compliance_status: "Perlu Verifikasi",
  risk_score: 0,
  risk_trend: [0, 0, 0, 0, 0],
  watchlist_status: "Rendah",
  watchlist_reason: "Vendor belum teridentifikasi dari sinyal.",
  last_inspection_date: "-",
  repeated_issue_categories: [],
  coverage_notes: "Vendor perlu diidentifikasi melalui klarifikasi awal.",
  recommended_action: "Minta klarifikasi awal untuk mengidentifikasi vendor dan lokasi.",
};

const MANUAL_VENDOR_ID = "__manual__";
const UNKNOWN_LOCATION = "Belum teridentifikasi";
const MANUAL_VENDOR_LABEL = "Penyedia belum terdaftar / masukkan dari laporan";
const ASSIGNMENT_GOVERNANCE =
  "Kandidat penyedia dan penugasan disaring berdasarkan cakupan wilayah sebagai bantuan pra-verifikasi. Operator berwenang tetap mengonfirmasi keterkaitan dan tindakan lanjutan.";

export const INVESTIGATORS = fallbackInvestigators.map((item) => item.name);

function known(value?: string | null): string {
  const normalized = (value ?? "").trim();
  return normalized && normalized !== UNKNOWN_LOCATION ? normalized : "";
}

function assignmentMatches(item: AssignmentCandidate, region: string, district: string): boolean {
  if (!region) return item.national;
  if (item.national) return true;
  if (!item.provinces.includes(region)) return false;
  return !district || item.districts.length === 0 || item.districts.includes(district);
}

function findProvince(region: string): LocationRegistryEntry | undefined {
  return fallbackLocationRegistry.find((item) => item.province === region);
}

export function provinceOptions(): string[] {
  return fallbackLocationRegistry.map((item) => item.province);
}

export function districtOptions(region: string): string[] {
  return findProvince(known(region))?.districts.map((item) => item.name) ?? [];
}

export function schoolOptions(region: string, district: string): string[] {
  const province = findProvince(known(region));
  const normalizedDistrict = known(district);
  if (!province) return [];
  return province.districts
    .filter((item) => !normalizedDistrict || item.name === normalizedDistrict)
    .flatMap((item) => item.schools);
}

function locationVendorIds(region: string, district: string, school: string): Set<string> {
  const province = findProvince(region);
  if (!province) return new Set();
  const districtItems = province.districts.filter((item) => !district || item.name === district);
  if (!school) return new Set(districtItems.flatMap((item) => item.vendor_ids));

  const schoolItems = districtItems.filter((item) => item.schools.includes(school));
  // Sekolah yang diketik manual belum ada di registry; pertahankan kandidat
  // pada kabupaten/kota yang sudah dipilih agar operator tetap bisa memilih
  // kandidat lokal tanpa memaksa nama sekolah palsu.
  return new Set((schoolItems.length ? schoolItems : districtItems).flatMap((item) => item.vendor_ids));
}

export function getAssignmentOptions(region = "", district = "", school = ""): AssignmentOptions {
  const normalizedRegion = known(region);
  const normalizedDistrict = known(district);
  const normalizedSchool = known(school);
  const vendorIds = locationVendorIds(normalizedRegion, normalizedDistrict, normalizedSchool);
  const vendors = fallbackVendors
    .filter((vendor) => vendorIds.has(vendor.id))
    .sort((a, b) => a.name.localeCompare(b.name, "id"));
  const investigators = fallbackInvestigators.filter((item) => assignmentMatches(item, normalizedRegion, normalizedDistrict));
  const units = fallbackUnits.filter((item) => assignmentMatches(item, normalizedRegion, normalizedDistrict));
  const vendorMessage = !normalizedRegion
    ? "Lengkapi wilayah atau sekolah untuk menampilkan kandidat penyedia yang relevan."
    : vendors.length === 0
      ? "Belum ada kandidat penyedia pada registry wilayah ini."
      : undefined;
  return {
    locations: fallbackLocationRegistry,
    vendors,
    investigators,
    units,
    vendor_message: vendorMessage,
    manual_vendor: { id: MANUAL_VENDOR_ID, label: MANUAL_VENDOR_LABEL },
    governance_notice: ASSIGNMENT_GOVERNANCE,
  };
}

const PRIORITY_SCORE: Record<string, number> = { Kritis: 88, Tinggi: 78, Sedang: 58, Rendah: 38 };

export function getSignal(signalId: number): Signal | null {
  return fallbackSignals.find((s) => s.id === signalId) ?? null;
}

/** Kasus runtime yang sama-sama dibaca workflow review dan halaman detail. */
export function getCase(caseId: string): OversightCase | null {
  return fallbackCases.find((c) => c.case_id === caseId) ?? null;
}

/**
 * Sinkronkan snapshot kasus dari API ke store offline.
 * Ini hanya memperbarui memori browser; tidak menulis seed atau membuat
 * evidence sebelum endpoint review menyatakan fusion berhasil.
 */
export function syncCase(caseData: OversightCase): void {
  const index = fallbackCases.findIndex((c) => c.case_id === caseData.case_id);
  if (index >= 0) fallbackCases[index] = caseData;
  else fallbackCases.unshift(caseData);

  for (const evidence of caseData.evidence) {
    const existing = fallbackEvidence.findIndex((e) => e.id === evidence.id);
    if (existing >= 0) fallbackEvidence[existing] = evidence;
    else fallbackEvidence.push(evidence);
  }
  for (const event of caseData.audit_events) {
    const existing = fallbackAudit.findIndex((e) => e.id === event.id);
    if (existing >= 0) fallbackAudit[existing] = event;
    else fallbackAudit.push(event);
  }
  for (const signal of caseData.signals) {
    const existing = fallbackSignals.findIndex((s) => s.id === signal.id);
    if (existing >= 0) fallbackSignals[existing] = signal;
  }
}

const STOP = new Set([
  "di", "dan", "yang", "pada", "sebuah", "porsi", "kasus", "sinyal", "laporan",
  "ada", "anak", "dugaan", "makanan", "menyebut", "unggahan", "lokasi", "belum",
  "pengawas", "media", "sosial",
]);
function words(text: string): Set<string> {
  return new Set((text || "").toLowerCase().split(/\s+/).map((w) => w.replace(/[.,;:]/g, "")).filter((w) => w.length > 2 && !STOP.has(w)));
}
function sharedKeywords(a: string, b: string): string[] {
  const wa = words(a);
  const out: string[] = [];
  for (const w of words(b)) if (wa.has(w)) out.push(w);
  return out;
}
function keywordOverlap(a: string, b: string): boolean {
  return sharedKeywords(a, b).length >= 1;
}
function daysBetween(a: string, b: string): number {
  return Math.abs(Date.parse(a) - Date.parse(b)) / 86_400_000;
}
function hoursBetween(a: string, b: string): number {
  return Math.abs(Date.parse(a) - Date.parse(b)) / 3_600_000;
}

export interface CaseCandidate {
  case_id: string;
  case_number: string;
  title: string;
  vendor_name: string;
  region: string;
  school: string;
  issue_category: string;
  priority_label: string;
  created_at: string;
  match_score: number;
  reasons: string[];
}
export interface SignalCandidate {
  id: number;
  summary: string;
  source: string;
  region: string;
  created_at: string;
  match_score: number;
  reasons: string[];
  attachment_path?: string;
  attachment_title?: string;
  label?: string;
}
export interface EvidenceCandidate {
  id: number;
  title: string;
  type: string;
  file_path?: string;
  case_id: string;
  confidence_score: number;
  match_score: number;
  reasons: string[];
}
export interface RelatedResult {
  signal_id: number;
  source_note: string;
  case_candidates: CaseCandidate[];
  signal_candidates: SignalCandidate[];
  evidence_candidates: EvidenceCandidate[];
  ai_notice: string;
}

export function findRelated(signalId: number): RelatedResult {
  const sig = getSignal(signalId)!;
  const issue = sig.issue_category || "";
  const region = sig.region || "";
  const school = sig.school || "";
  const summary = sig.summary || "";
  const time = sig.created_at || "";

  const caseCands: CaseCandidate[] = [];
  for (const c of fallbackCases) {
    let score = 0;
    const reasons: string[] = [];
    if (sig.vendor_id && sig.vendor_id === c.vendor_id) { score += 45; reasons.push("Vendor yang sama"); }
    if (issue && issue === c.issue_category) { score += 25; reasons.push("Kategori isu sama"); }
    if (region && region === c.region) { score += 15; reasons.push("Wilayah serupa"); }
    if (school && school === c.school) { score += 15; reasons.push("Sekolah serupa"); }
    if (keywordOverlap(summary, c.title)) { score += 15; reasons.push("Kata kunci isu serupa"); }
    if (time && c.created_at && daysBetween(time, c.created_at) <= 3) { score += 10; reasons.push("Waktu laporan berdekatan"); }
    if (score === 0 && keywordOverlap(summary, `${c.issue_category} ${c.school}`)) { score += 8; reasons.push("Kemiripan konteks"); }
    if (score > 0) {
      caseCands.push({
        case_id: c.case_id, case_number: c.case_number ?? caseNumber(c.case_id), title: c.title,
        vendor_name: c.vendor_name, region: c.region, school: c.school, issue_category: c.issue_category,
        priority_label: c.priority_label, created_at: c.created_at, match_score: Math.min(score, 95), reasons,
      });
    }
  }
  caseCands.sort((a, b) => b.match_score - a.match_score);

  const sigText = sig.text || "";
  const sigDistrict = sig.district || "";
  const signalCands: SignalCandidate[] = [];
  for (const o of fallbackSignals) {
    if (o.id === signalId || o.case_id) continue;
    let score = 0;
    const reasons: string[] = [];
    const shared = sharedKeywords(`${summary} ${sigText}`, `${o.summary} ${o.text ?? ""}`);
    if (shared.length) { score += 30; reasons.push(`Kata kunci isu serupa: ${shared.slice(0, 3).join(", ")}`); }
    else if (keywordOverlap(summary, o.summary)) { score += 20; reasons.push("Kata kunci isu serupa"); }
    if (region && region === o.region) { score += 20; reasons.push(`Wilayah provinsi sama: ${region}`); }
    if (o.created_at && time && hoursBetween(time, o.created_at) <= 48) { score += 10; reasons.push("Waktu publikasi berdekatan"); }
    const oDistrict = o.district || "";
    if (sigDistrict && (!oDistrict || oDistrict === "Belum teridentifikasi")) reasons.push("Lokasi sekolah/kabupaten pada sinyal ini belum terkonfirmasi");
    if (score > 0) signalCands.push({
      id: o.id, summary: o.summary, source: o.source, region: o.region,
      created_at: o.created_at, match_score: Math.min(score, 60), reasons,
      attachment_path: o.attachment_path, attachment_title: o.attachment_title,
      label: "Kandidat sinyal pendukung — perlu peninjauan operator",
    });
  }
  signalCands.sort((a, b) => b.match_score - a.match_score);

  const evCands: EvidenceCandidate[] = [];
  for (const ev of fallbackEvidence) {
    const c = fallbackCases.find((x) => x.case_id === ev.case_id);
    let score = 0;
    const reasons: string[] = [];
    if (issue && c && issue === c.issue_category) { score += 30; reasons.push("Kategori isu sama"); }
    if (keywordOverlap(summary, ev.title)) { score += 15; reasons.push("Kata kunci isu serupa"); }
    if (score > 0) evCands.push({
      id: ev.id, title: ev.title, type: ev.type, file_path: ev.file_path, case_id: ev.case_id,
      confidence_score: ev.confidence_score, match_score: Math.min(score, 90), reasons,
    });
  }
  evCands.sort((a, b) => b.match_score - a.match_score);

  return {
    signal_id: signalId,
    source_note: "Hasil dari sumber data demo/internal, bukan crawling real-time.",
    case_candidates: caseCands.slice(0, 5),
    signal_candidates: signalCands.slice(0, 5),
    evidence_candidates: evCands.slice(0, 6),
    ai_notice: GOVERNANCE,
  };
}

export interface Assessment {
  severity_score: number;
  confidence_score: number;
  nutrition_concern_score: number;
  cost_anomaly_score: number;
  anomaly_score: number;
  final_priority_score: number;
  priority_label: string;
  explanation: string;
  recommended_action: string;
  ai_notice: string;
}

export function initialAssessment(signalId: number): Assessment {
  const sig = getSignal(signalId)!;
  const conf = Math.round((sig.source_confidence ?? 0.4) * 100);
  const base = PRIORITY_SCORE[sig.urgency] ?? 45;
  const nutrition = (sig.issue_category || "").includes("protein") || (sig.summary || "").toLowerCase().includes("gizi") ? 50 : 30;
  const cost = (sig.issue_category || "").includes("biaya") ? 40 : 20;
  const recurrence = 30;
  const final = Math.min(95, Math.round(base * 0.5 + conf * 0.2 + nutrition * 0.15 + cost * 0.1 + recurrence * 0.05));
  const label = final >= 80 ? "Kritis" : final >= 65 ? "Tinggi" : final >= 45 ? "Sedang" : "Rendah";
  return {
    severity_score: base, confidence_score: conf, nutrition_concern_score: nutrition,
    cost_anomaly_score: cost, anomaly_score: recurrence, final_priority_score: final, priority_label: label,
    explanation:
      "Penilaian awal sistem (pra-verifikasi) berdasar sumber, keyakinan awal, dan kategori sinyal. Nilai ini bukan keputusan final; operator dapat menyesuaikan dengan justifikasi.",
    recommended_action: sig.vendor_id
      ? "Kumpulkan bukti tambahan sebelum verifikasi lapangan."
      : "Minta klarifikasi awal untuk mengidentifikasi vendor dan lokasi.",
    ai_notice: GOVERNANCE,
  };
}

export interface ReviewPayload {
  decision: "merge" | "create" | "defer";
  searched_related?: boolean;
  target_case_id?: string | null;
  new_case?: {
    title?: string;
    issue_category?: string;
    vendor_id?: string;
    vendor_name?: string;
    vendor_source_note?: string;
    region?: string;
    district?: string;
    school?: string;
    summary?: string;
  };
  defer_reason?: string;
  selected_signal_ids?: number[];
  selected_evidence_ids?: number[];
  assignment?: { investigator?: string; unit?: string; urgency?: string; sla?: string; reviewer_note?: string; recommended_action?: string };
  override?: {
    operator_adjusted?: boolean; priority_label?: string; final_priority_score?: number;
    severity_score?: number; confidence_score?: number; nutrition_concern_score?: number;
    cost_anomaly_score?: number; anomaly_score?: number; override_reason?: string;
  };
}

export interface ReviewResult {
  outcome: "merged" | "created" | "deferred";
  case_id?: string;
  case_number?: string;
  signal_id?: number;
  redirect: string;
  case?: OversightCase;
  audit_events: AuditTrailEvent[];
  ai_notice: string;
}

function nowIso() { return new Date().toISOString(); }
function nextAuditId() { return (fallbackAudit.reduce((m, a) => Math.max(m, a.id), 0) + 1); }
function addAudit(caseId: string, eventType: string, description: string, actor = "Operator Demo", role = "Operator Distrik"): AuditTrailEvent {
  const ev: AuditTrailEvent = { id: nextAuditId(), case_id: caseId, ticket_id: "", event_type: eventType, actor, role, description, timestamp: nowIso() };
  fallbackAudit.unshift(ev);
  return ev;
}

function nextCaseId(): string {
  const nums = fallbackCases.map((c) => parseInt(c.case_id.replace(/\D/g, ""), 10) || 0);
  return `case-${String(Math.max(0, ...nums) + 1).padStart(3, "0")}`;
}

function nextEvidenceId() { return fallbackEvidence.reduce((m, e) => Math.max(m, e.id), 0) + 1; }
function evidenceFromSignal(caseId: string, sig: Signal) {
  if (!sig.attachment_path) return null;
  const ev = {
    id: nextEvidenceId(), case_id: caseId, signal_id: sig.id, type: "photo",
    title: sig.attachment_title || "Lampiran sinyal", file_path: sig.attachment_path,
    linked_entity: caseNumber(caseId), source: sig.attachment_source || sig.source || "Sinyal",
    confidence_score: Math.round((sig.source_confidence ?? 0.5) * 100) / 100,
    review_status: "Perlu Ditinjau",
    reviewer_note: sig.attachment_note || "Lampiran sinyal sebagai bukti pra-verifikasi; perlu ditinjau operator.",
    created_at: nowIso(),
  };
  fallbackEvidence.push(ev);
  return ev;
}

function effectiveLocation(signal: Signal, newCase: ReviewPayload["new_case"]): { region: string; district: string; school: string } {
  const data = newCase ?? {};
  const value = (key: "region" | "district" | "school", fallback: string) =>
    Object.prototype.hasOwnProperty.call(data, key)
      ? (known(data[key]) || UNKNOWN_LOCATION)
      : (known(fallback) || UNKNOWN_LOCATION);
  return {
    region: value("region", signal.region),
    district: value("district", signal.district),
    school: value("school", signal.school),
  };
}

function validateOfflineAssignment(
  region: string,
  district: string,
  school: string,
  newCase: ReviewPayload["new_case"],
  assignment: NonNullable<ReviewPayload["assignment"]>,
): void {
  const options = getAssignmentOptions(region, district, school);
  const requestedVendorId = newCase?.vendor_id || "vnd-unknown";
  if (requestedVendorId === MANUAL_VENDOR_ID && !(newCase?.vendor_name ?? "").trim()) {
    throw new Error("Nama penyedia wajib diisi untuk opsi penyedia manual.");
  }
  if (requestedVendorId !== "vnd-unknown" && requestedVendorId !== MANUAL_VENDOR_ID && !options.vendors.some((vendor) => vendor.id === requestedVendorId)) {
    throw new Error("Vendor tidak sesuai dengan cakupan wilayah kasus.");
  }
  if (assignment.investigator && !options.investigators.some((item) => item.name === assignment.investigator)) {
    throw new Error("Investigator tidak sesuai dengan cakupan wilayah kasus.");
  }
  if (assignment.unit && !options.units.some((item) => item.name === assignment.unit)) {
    throw new Error("Unit penanggung jawab tidak sesuai dengan cakupan wilayah kasus.");
  }
}

export function reviewSignal(signalId: number, p: ReviewPayload): ReviewResult {
  const sig = getSignal(signalId);
  if (!sig) throw new Error("Sinyal tidak ditemukan");
  if (sig.case_id) throw new Error("Sinyal sudah terhubung ke kasus.");

  const isSocial = (sig.source || "").toLowerCase().includes("sosial");
  const actor = "Operator Demo";
  const audit: AuditTrailEvent[] = [];
  // Peristiwa global (case_id kosong) tidak muncul di kasus tertentu.
  audit.push(addAudit("", isSocial ? "social_signal_reviewed" : "signal_reviewed",
    `Sinyal #${signalId} ditinjau operator.${isSocial ? " Sinyal media sosial diperiksa sebagai sinyal pendukung, bukan bukti final." : ""}`, actor));
  if (p.searched_related) audit.push(addAudit("", "related_items_searched", "Operator mencari sinyal, laporan, dan bukti terkait.", actor));

  const assign = p.assignment ?? {};
  const ov = p.override ?? {};

  if (p.decision === "merge") {
    const target = fallbackCases.find((c) => c.case_id === p.target_case_id);
    if (!target) throw new Error("Kasus target tidak ditemukan.");
    const targetRegion = known(target.region);
    const targetDistrict = known(target.district);
    const targetSchool = known(target.school);
    const options = getAssignmentOptions(targetRegion, targetDistrict, targetSchool);
    if (assign.investigator && !options.investigators.some((item) => item.name === assign.investigator)) {
      throw new Error("Investigator tidak sesuai dengan cakupan wilayah kasus.");
    }
    if (assign.unit && !options.units.some((item) => item.name === assign.unit)) {
      throw new Error("Unit penanggung jawab tidak sesuai dengan cakupan wilayah kasus.");
    }
    sig.case_id = target.case_id;
    sig.status = "Terhubung ke Kasus";
    sig.issue_category = target.issue_category;
    // signal_merged: penggabungan diterima OPERATOR (bukan otomatis).
    const mergeEv = addAudit(target.case_id, "signal_merged",
      `Operator ${actor} menggabungkan sinyal #${signalId} ke ${target.case_number ?? caseNumber(target.case_id)} sebagai sinyal pendukung. Keterkaitan lokasi/waktu belum dikonfirmasi dan tetap memerlukan verifikasi.`,
      actor);
    target.audit_events = [mergeEv, ...target.audit_events];
    audit.push(mergeEv);
    const ev = evidenceFromSignal(target.case_id, sig);
    if (ev) {
      target.evidence = [...target.evidence, ev];
      target.evidence_count += 1;
      if (target.ticket && !target.ticket.linked_evidence_ids.includes(ev.id)) {
        target.ticket = {
          ...target.ticket,
          linked_evidence_ids: [...target.ticket.linked_evidence_ids, ev.id],
        };
      }
      const evAudit = addAudit(target.case_id, "evidence_added", `Bukti '${ev.title}' (sumber ${ev.source}) ditambahkan dari sinyal #${signalId}. Status: Perlu Ditinjau.`, actor);
      target.audit_events = [evAudit, ...target.audit_events];
      audit.push(evAudit);
    }
    if (ov.operator_adjusted && ov.final_priority_score != null) {
      target.score.final_priority_score = ov.final_priority_score;
      target.score.priority_label = ov.priority_label ?? target.score.priority_label;
      target.priority_label = ov.priority_label ?? target.priority_label;
      const rr = addAudit(target.case_id, "risk_reassessed", `Rekomendasi pra-verifikasi: skor diperbarui menjadi ${ov.final_priority_score} (${ov.priority_label ?? "-"}) setelah tambahan sinyal. Operator dapat override. Alasan: ${ov.override_reason ?? "-"}.`, actor);
      target.audit_events = [rr, ...target.audit_events];
      audit.push(rr);
    }
    if (assign.investigator) {
      const before = target.assigned_investigator || "Belum ditetapkan";
      target.assigned_investigator = assign.investigator;
      const iev = addAudit(target.case_id, "investigator_assigned", `Investigator ditetapkan. Sebelum: ${before}; sesudah: ${assign.investigator}.`, assign.investigator);
      target.audit_events = [iev, ...target.audit_events];
      audit.push(iev);
    }
    if (assign.unit) {
      const before = target.assigned_unit || "Belum ditetapkan";
      target.assigned_unit = assign.unit;
      const uev = addAudit(target.case_id, "responsible_unit_assigned", `Unit penanggung jawab ditetapkan. Sebelum: ${before}; sesudah: ${assign.unit}.`, actor);
      target.audit_events = [uev, ...target.audit_events];
      audit.push(uev);
    }
    target.signals_count += 1;
    target.signals = [...target.signals, sig];
    target.updated_at = nowIso();
    return { outcome: "merged", case_id: target.case_id, case_number: target.case_number ?? caseNumber(target.case_id), redirect: `/cases/${target.case_id}`, case: target, audit_events: audit, ai_notice: GOVERNANCE };
  }

  if (p.decision === "create") {
    const nc = p.new_case ?? {};
    const { region, district, school } = effectiveLocation(sig, nc);
    const vendorId = nc.vendor_id || sig.vendor_id || "vnd-unknown";
    validateOfflineAssignment(region, district, school, { ...nc, vendor_id: vendorId }, assign);
    const vendor = fallbackVendors.find((v) => v.id === vendorId) ?? UNKNOWN_VENDOR;
    const manualVendor = vendorId === MANUAL_VENDOR_ID;
    const vendorName = manualVendor ? (nc.vendor_name ?? "").trim() : vendor.name;
    const resolvedVendorId = manualVendor ? UNKNOWN_VENDOR.id : vendor.id;
    const cid = nextCaseId();
    const assess = initialAssessment(signalId);
    const finalScore = ov.final_priority_score ?? assess.final_priority_score;
    const label = ov.priority_label ?? assess.priority_label;
    const score: ScoreResult = {
      id: fallbackCases.length + 1,
      case_id: cid, vendor_id: resolvedVendorId, vendor_name: vendorName || vendor.name, region,
      severity_score: ov.severity_score ?? assess.severity_score,
      confidence_score: ov.confidence_score ?? assess.confidence_score,
      nutrition_concern_score: ov.nutrition_concern_score ?? assess.nutrition_concern_score,
      cost_anomaly_score: ov.cost_anomaly_score ?? assess.cost_anomaly_score,
      anomaly_score: ov.anomaly_score ?? assess.anomaly_score,
      final_priority_score: finalScore, priority_label: label,
      explanation: assess.explanation, recommended_action: assign.recommended_action ?? assess.recommended_action,
      computed_at: nowIso(), ai_notice: GOVERNANCE,
    };
    const createdEv = addAudit(cid, "case_created", `Kasus ${caseNumber(cid)} dibentuk dari sinyal #${signalId}.`, actor);
    audit.push(createdEv);
    const caseAudit: AuditTrailEvent[] = [createdEv];
    // Lampiran laporan resmi menjadi bukti utama kasus.
    const reportEv = evidenceFromSignal(cid, sig);
    if (reportEv) {
      const evAudit = addAudit(cid, "evidence_added", `Bukti '${reportEv.title}' (sumber ${reportEv.source}) ditambahkan dari sinyal #${signalId}. Status: Perlu Ditinjau.`, actor);
      audit.push(evAudit); caseAudit.unshift(evAudit);
    }
    if (ov.operator_adjusted) {
      const ev = addAudit(cid, "risk_overridden", `Prioritas disesuaikan operator menjadi ${label} (skor ${finalScore}). Alasan: ${ov.override_reason ?? "-"}.`, actor);
      audit.push(ev); caseAudit.unshift(ev);
    }
    if (assign.investigator) {
      const ev = addAudit(cid, "investigator_assigned", `Investigator ditetapkan. Sebelum: Belum ditetapkan; sesudah: ${assign.investigator}. Urgensi ${assign.urgency ?? "-"}, SLA usulan ${assign.sla ?? "-"}.`, assign.investigator);
      audit.push(ev); caseAudit.unshift(ev);
    }

    const locationEv = addAudit(cid, "location_updated", `Lokasi kasus ditetapkan. Sebelum: dari sinyal; sesudah: ${region} → ${district} → ${school}.`, actor);
    audit.push(locationEv); caseAudit.unshift(locationEv);
    if (manualVendor) {
      const ev = addAudit(cid, "vendor_entered_from_report", `Penyedia dimasukkan dari laporan. Sebelum: Belum teridentifikasi; sesudah: ${vendorName}. Catatan sumber: ${nc.vendor_source_note?.trim() || "-"}.`, actor);
      audit.push(ev); caseAudit.unshift(ev);
    } else if (resolvedVendorId === "vnd-unknown") {
      const ev = addAudit(cid, "vendor_marked_unidentified", "Penyedia tetap Belum teridentifikasi; operator tidak dipaksa memilih vendor acak.", actor);
      audit.push(ev); caseAudit.unshift(ev);
    } else {
      const ev = addAudit(cid, "vendor_candidate_selected", `Kandidat penyedia dipilih. Sebelum: Belum teridentifikasi; sesudah: ${vendor.name}. Kandidat berdasarkan cakupan layanan wilayah. Konfirmasi operator tetap diperlukan.`, actor);
      audit.push(ev); caseAudit.unshift(ev);
    }
    if (assign.unit) {
      const ev = addAudit(cid, "responsible_unit_assigned", `Unit penanggung jawab ditetapkan. Sebelum: Belum ditetapkan; sesudah: ${assign.unit}.`, actor);
      audit.push(ev); caseAudit.unshift(ev);
    }

    const newCase: OversightCase = {
      id: cid, case_id: cid, case_number: caseNumber(cid),
      title: nc.title || `Tinjauan sinyal: ${sig.summary.slice(0, 80)}`,
      priority_label: label, status: "Sedang Ditinjau",
      vendor_id: resolvedVendorId, vendor_name: vendorName || vendor.name, vendor_source_note: manualVendor ? (nc.vendor_source_note?.trim() || null) : null,
      region, district,
      school,
      issue_category: nc.issue_category || sig.issue_category || "belum diklasifikasi",
      sla_status: "SLA 72h", assigned_unit: assign.unit || "Unit Pengawasan Vendor MBG Nasional", assigned_investigator: assign.investigator || null,
      recommended_action: score.recommended_action,
      summary: nc.summary || sig.text || sig.summary,
      what_happened: `Kasus ${caseNumber(cid)} dibentuk dari sinyal intake #${signalId} setelah tinjauan operator.`,
      why_it_matters: `Kasus menyangkut ${nc.school || sig.school || "lokasi belum teridentifikasi"} dan memerlukan klarifikasi awal.`,
      risk_explanation: score.explanation,
      signals_count: 1, evidence_count: reportEv ? 1 : 0, ticket_id: null,
      created_at: nowIso(), updated_at: nowIso(),
      vendor: manualVendor ? UNKNOWN_VENDOR : vendor, signals: [sig], complaints: [], reports: [], daily_reports: [], evidence: reportEv ? [reportEv] : [],
      score, ticket: null,
      copilot_sources: [{ label: "Kasus", source_type: "case", source_id: cid, title: caseNumber(cid) }],
      audit_events: caseAudit, ai_notice: GOVERNANCE,
    };
    fallbackCases.unshift(newCase);
    sig.case_id = cid; sig.status = "Terhubung ke Kasus"; sig.issue_category = newCase.issue_category;
    return { outcome: "created", case_id: cid, case_number: caseNumber(cid), redirect: `/cases/${cid}`, case: newCase, audit_events: audit, ai_notice: GOVERNANCE };
  }

  // defer
  if (!p.defer_reason) throw new Error("Alasan/catatan reviewer wajib diisi saat menunda.");
  sig.status = "Perlu Ditinjau";
  audit.push(addAudit("", "review_deferred", `Sinyal #${signalId} disimpan sebagai perlu ditinjau. Catatan: ${p.defer_reason}.`));
  return { outcome: "deferred", signal_id: signalId, redirect: "/intake", audit_events: audit, ai_notice: GOVERNANCE };
}
