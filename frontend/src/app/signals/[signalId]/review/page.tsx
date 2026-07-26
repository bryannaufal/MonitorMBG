"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ClipboardCheck,
  FileSearch,
  GitMerge,
  Inbox,
  ShieldAlert,
  UserCog,
} from "lucide-react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { api } from "@/lib/api";
import * as store from "@/lib/reviewStore";
import * as overlay from "@/lib/runtimeOverlay";
import type { AssignmentOptions, Signal } from "@/types/monitoring";

type Decision = "merge" | "create" | "defer";
const MANUAL_VENDOR_ID = "__manual__";
const MANUAL_SCHOOL_ID = "__manual_school__";
const UNKNOWN_LOCATION = "Belum teridentifikasi";

export default function SignalReviewPage() {
  const params = useParams<{ signalId: string }>();
  const router = useRouter();
  const signalId = Number(params.signalId);

  const [signal, setSignal] = useState<Signal | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [offline, setOffline] = useState(false);
  const [alreadyLinked, setAlreadyLinked] = useState<string | null>(null);

  // Temuan terkait
  const [searching, setSearching] = useState(false);
  const [related, setRelated] = useState<store.RelatedResult | null>(null);
  const [selCases, setSelCases] = useState<Set<string>>(new Set());
  const [selSignals, setSelSignals] = useState<Set<number>>(new Set());
  const [selEvidence, setSelEvidence] = useState<Set<number>>(new Set());

  // Keputusan
  const [decision, setDecision] = useState<Decision>("create");
  const [targetCase, setTargetCase] = useState<string>("");
  const [ncTitle, setNcTitle] = useState("");
  const [ncIssue, setNcIssue] = useState("");
  const [ncVendor, setNcVendor] = useState("");
  const [ncManualVendorName, setNcManualVendorName] = useState("");
  const [ncManualVendorNote, setNcManualVendorNote] = useState("");
  const [ncRegion, setNcRegion] = useState("");
  const [ncDistrict, setNcDistrict] = useState("");
  const [ncSchool, setNcSchool] = useState("");
  const [schoolManual, setSchoolManual] = useState(false);
  const [ncSummary, setNcSummary] = useState("");
  const [ncCaseType, setNcCaseType] = useState("Oversight");
  const [ncCaseSubtype, setNcCaseSubtype] = useState("");
  const [ncImpact, setNcImpact] = useState("");
  const [handlingStrategy, setHandlingStrategy] = useState<"direct" | "single_ticket" | "multi_ticket">("direct");
  const [relatedCaseId, setRelatedCaseId] = useState("");
  const [caseRelationship, setCaseRelationship] = useState("related");
  const [deferReason, setDeferReason] = useState("");

  // Penilaian & override
  const [assessment, setAssessment] = useState<store.Assessment | null>(null);
  const [ovPriority, setOvPriority] = useState("Sedang");
  const [ovScore, setOvScore] = useState(45);
  const [ovReason, setOvReason] = useState("");

  // Penugasan
  const [assignmentOptions, setAssignmentOptions] = useState<AssignmentOptions>(store.getAssignmentOptions("", "", ""));
  const [assignmentLoading, setAssignmentLoading] = useState(false);
  const [locationNotice, setLocationNotice] = useState<string | null>(null);
  const optionsRequest = useRef(0);
  const [investigator, setInvestigator] = useState("");
  const [unit, setUnit] = useState("");
  const [secondaryOwner, setSecondaryOwner] = useState("");
  const [watchers, setWatchers] = useState("");
  const [urgency, setUrgency] = useState("Sedang");
  const [reviewerNote, setReviewerNote] = useState("");
  const [recommended, setRecommended] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(null);

  async function refreshAssignmentOptions(region: string, district: string, school: string) {
    const requestId = ++optionsRequest.current;
    setAssignmentLoading(true);
    try {
      const query = new URLSearchParams();
      if (region) query.set("region", region);
      if (district) query.set("district", district);
      if (school) query.set("school", school);
      const suffix = query.toString() ? `?${query.toString()}` : "";
      const options = await api.get<AssignmentOptions>(`/signals/assignment-options${suffix}`);
      if (requestId !== optionsRequest.current) return;
      setAssignmentOptions(options);
    } catch {
      if (requestId !== optionsRequest.current) return;
      setOffline(true);
      setAssignmentOptions(store.getAssignmentOptions(region, district, school));
    } finally {
      if (requestId === optionsRequest.current) setAssignmentLoading(false);
    }
  }

  function updateLocation(region: string, district: string, school: string, manualSchool = false) {
    const changed = region !== ncRegion || district !== ncDistrict || school !== ncSchool;
    setNcRegion(region);
    setNcDistrict(district);
    setNcSchool(school);
    setSchoolManual(manualSchool);
    setNcVendor("");
    setNcManualVendorName("");
    setNcManualVendorNote("");
    setInvestigator("");
    setUnit("");
    setAssignmentOptions(store.getAssignmentOptions(region, district, school));
    if (changed) setLocationNotice("Wilayah berubah; pilihan vendor dan penugasan perlu disesuaikan.");
    void refreshAssignmentOptions(region, district, school);
  }

  useEffect(() => {
    async function load() {
      let sig: Signal | null = null;
      try {
        sig = await api.get<Signal>(`/signals/${signalId}`);
      } catch {
        setOffline(true);
        sig = store.getSignal(signalId);
      }
      if (!sig) { setNotFound(true); setLoading(false); return; }
      // Overlay runtime menang: bila operator sudah menautkan sinyal ini pada
      // sesi ini (meski API mengembalikan seed pasca-restart), hormati tautannya.
      sig = overlay.applySignals([sig])[0];
      if (sig.case_id) { setAlreadyLinked(sig.case_id); setSignal(sig); setLoading(false); return; }
      setSignal(sig);

      // Prefill kasus baru dari sinyal.
      setNcTitle(`Tinjauan sinyal: ${sig.summary.slice(0, 80)}`);
      setNcIssue(sig.issue_category && sig.issue_category !== "belum diklasifikasi" ? sig.issue_category : "");
      // Review dimulai dari placeholder; vendor sumber tidak dipaksakan
      // menjadi pilihan kandidat sebelum operator mengonfirmasinya.
      setNcVendor("");
      const initialRegion = sig.region !== UNKNOWN_LOCATION ? (sig.region ?? "") : "";
      const initialDistrict = sig.district !== UNKNOWN_LOCATION ? (sig.district ?? "") : "";
      const initialSchool = sig.school !== UNKNOWN_LOCATION ? (sig.school ?? "") : "";
      setNcRegion(initialRegion);
      setNcDistrict(initialDistrict);
      setNcSchool(initialSchool);
      setSchoolManual(Boolean(initialSchool && !store.schoolOptions(initialRegion, initialDistrict).includes(initialSchool)));
      setNcSummary(sig.text ?? sig.summary);
      setUrgency(sig.urgency ?? "Sedang");
      setReviewerNote("");
      await refreshAssignmentOptions(initialRegion, initialDistrict, initialSchool);

      // Penilaian awal.
      let a: store.Assessment;
      try {
        a = await api.get<store.Assessment>(`/signals/${signalId}/assessment`);
      } catch {
        setOffline(true);
        a = store.initialAssessment(signalId);
      }
      setAssessment(a);
      setOvPriority(a.priority_label);
      setOvScore(a.final_priority_score);
      setRecommended(a.recommended_action);
      setLoading(false);
    }
    load();
  }, [signalId]);

  // Mengikuti SLA_POLICIES di app/ticketing.py. Urgensi tak dikenal jatuh ke
  // P3 (48h) — sama dengan default backend, bukan 72h.
  const sla = useMemo(
    () => ({ Kritis: "4h", Tinggi: "24h", Sedang: "48h", Rendah: "72h" }[urgency] ?? "48h"),
    [urgency],
  );
  const overrideAdjusted = useMemo(
    () => Boolean(assessment) && (ovPriority !== assessment!.priority_label || ovScore !== assessment!.final_priority_score),
    [assessment, ovPriority, ovScore],
  );

  async function runSearch() {
    setSearching(true);
    setRelated(null);
    // Loading singkat yang jelas.
    await new Promise((r) => setTimeout(r, 700));
    let rel: store.RelatedResult;
    try {
      rel = await api.post<store.RelatedResult, Record<string, never>>(`/signals/${signalId}/related`, {});
    } catch {
      setOffline(true);
      rel = store.findRelated(signalId);
    }
    setRelated(rel);
    setSearching(false);
  }

  function toggle<T>(set: React.Dispatch<React.SetStateAction<Set<T>>>, value: T) {
    set((prev) => {
      const next = new Set(prev);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return next;
    });
  }

  function validate(): string | null {
    if (decision === "merge" && !targetCase) return "Pilih satu kasus target untuk digabungkan.";
    if (decision === "create" && !ncTitle.trim()) return "Judul kasus wajib diisi.";
    if (decision === "defer" && !deferReason.trim()) return "Alasan/catatan reviewer wajib diisi saat menunda.";
    if (overrideAdjusted && !ovReason.trim()) return "Alasan override wajib diisi bila prioritas/skor diubah.";
    return null;
  }

  async function submit() {
    const err = validate();
    if (err) { setResult({ ok: false, text: err }); return; }
    setSubmitting(true);
    setResult(null);

    const payload: store.ReviewPayload = {
      decision,
      searched_related: Boolean(related),
      target_case_id: decision === "merge" ? targetCase : undefined,
      new_case: decision === "create" ? {
        title: ncTitle,
        issue_category: ncIssue,
        vendor_id: ncVendor || "vnd-unknown",
        vendor_name: ncVendor === MANUAL_VENDOR_ID ? ncManualVendorName : undefined,
        vendor_source_note: ncVendor === MANUAL_VENDOR_ID ? ncManualVendorNote : undefined,
        region: ncRegion || UNKNOWN_LOCATION,
        district: ncDistrict || UNKNOWN_LOCATION,
        school: ncSchool || UNKNOWN_LOCATION,
        summary: ncSummary,
        case_type: ncCaseType,
        case_subtype: ncCaseSubtype || undefined,
        impact_summary: ncImpact || ncSummary,
        handling_strategy: handlingStrategy,
        related_case_id: relatedCaseId || undefined,
        case_relationship: relatedCaseId ? caseRelationship : undefined,
      } : undefined,
      defer_reason: decision === "defer" ? deferReason : undefined,
      selected_signal_ids: [...selSignals],
      selected_evidence_ids: [...selEvidence],
      assignment: { investigator: investigator || undefined, unit, urgency, sla, reviewer_note: reviewerNote, recommended_action: recommended, secondary_owner: secondaryOwner || undefined, watchers: watchers.split(",").map((value) => value.trim()).filter(Boolean) },
      override: {
        operator_adjusted: overrideAdjusted, priority_label: ovPriority, final_priority_score: ovScore,
        override_reason: ovReason || undefined,
      },
    };

    let res: store.ReviewResult | null = null;
    try {
      res = await api.post<store.ReviewResult, store.ReviewPayload>(`/signals/${signalId}/review`, payload);
    } catch {
      try {
        setOffline(true);
        res = store.reviewSignal(signalId, payload);
      } catch (e) {
        setResult({ ok: false, text: e instanceof Error ? e.message : "Gagal menyimpan review." });
        setSubmitting(false);
        return;
      }
    }

    // Rekam mutasi ke overlay runtime agar bertahan lintas refresh / restart
    // backend, lalu sinkronkan store offline untuk mode tanpa API.
    if (res.case) {
      store.syncCase(res.case);
      overlay.recordCase(res.case);
    } else if (res.outcome === "merged" && res.case_id) {
      overlay.recordSignalLink(signalId, { case_id: res.case_id, case_number: res.case_number ?? null, status: "Terhubung ke Kasus" });
    }
    overlay.recordAudit(res.audit_events ?? []);
    setResult({ ok: true, text: outcomeText(res) });
    // Redirect setelah jeda singkat agar pesan sukses terbaca.
    setTimeout(() => router.push(res!.redirect), 900);
  }

  if (loading) return <LoadingState label="Memuat sinyal untuk ditinjau..." />;

  if (notFound) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Sinyal tidak ditemukan"
          description="ID sinyal yang diminta tidak tersedia."
          breadcrumbs={[{ label: "Pusat Kendali", href: "/" }, { label: "Kotak Masuk Sinyal", href: "/intake" }, { label: "Tinjau Sinyal" }]}
        />
        <section className="rounded-xl border border-border bg-surface-raised p-6 text-sm text-muted-foreground">
          <p className="break-words">
            Sinyal <span className="font-mono">#{params.signalId}</span> tidak ada dalam sistem. Sistem tidak membuka
            sinyal atau kasus lain secara diam-diam.
          </p>
          <Link href="/intake" className="mt-4 inline-flex items-center gap-2 rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">
            <Inbox className="h-4 w-4" /> Kembali ke Kotak Masuk Sinyal
          </Link>
        </section>
      </div>
    );
  }

  if (alreadyLinked && signal) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Sinyal sudah terhubung"
          description="Sinyal ini sudah memiliki kasus. Buka kasusnya langsung."
          breadcrumbs={[{ label: "Pusat Kendali", href: "/" }, { label: "Kotak Masuk Sinyal", href: "/intake" }, { label: "Tinjau Sinyal" }]}
        />
        <section className="rounded-xl border border-border bg-surface-raised p-6 text-sm text-muted-foreground">
          <p className="break-words">Sinyal #{signal.id} sudah terhubung ke sebuah kasus.</p>
          <Link href={`/cases/${alreadyLinked}`} className="mt-4 inline-flex rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">
            Buka Kasus
          </Link>
        </section>
      </div>
    );
  }

  const sig = signal!;
  const provinceItems = assignmentOptions.locations;
  const districtItems = provinceItems.find((item) => item.province === ncRegion)?.districts ?? [];
  const schoolItems = store.schoolOptions(ncRegion, ncDistrict);
  const selectedVendor = assignmentOptions.vendors.find((vendor) => vendor.id === ncVendor);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tinjau & Bentuk Kasus"
        description="Operator menilai keterkaitan sinyal, bukti, dan laporan sebelum kasus dibentuk. Belum ada kasus atau tiket yang dibuat sampai Anda mengonfirmasi."
        breadcrumbs={[{ label: "Pusat Kendali", href: "/" }, { label: "Kotak Masuk Sinyal", href: "/intake" }, { label: "Tinjau Sinyal" }]}
        source={offline ? "fallback" : "api"}
      />
      <div className="rounded-lg border border-brand-500/30 bg-brand-500/10 p-4 text-sm text-brand-800 dark:text-brand-100">
        Pencocokan dan penilaian pada halaman ini adalah sinyal pra-verifikasi. Operator berwenang menentukan apakah
        temuan terkait, membentuk kasus, dan menetapkan tindak lanjut.
      </div>

      {/* 1. Ringkasan Signal Masuk */}
      <SectionCard icon={Inbox} title="1. Ringkasan Sinyal Masuk">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap gap-2">
              <StatusBadge label={sig.status} />
              <StatusBadge label={sig.urgency} />
              <StatusBadge label={sig.issue_category} />
            </div>
            <p className="mt-4 max-w-3xl break-words text-sm font-medium">{sig.summary}</p>
            <p className="mt-2 max-w-3xl break-words text-sm leading-6 text-muted-foreground">{sig.text}</p>
            {sig.attachment_path ? (
              <div className="mt-4 max-w-md">
                <div className="relative aspect-video w-full overflow-hidden rounded-md border border-border bg-surface-overlay">
                  <Image src={sig.attachment_path} alt={sig.attachment_title ?? "Lampiran sinyal"} fill unoptimized className="object-cover" sizes="(max-width: 768px) 100vw, 400px" />
                </div>
                <p className="mt-2 break-words text-xs text-muted-foreground">
                  {sig.attachment_title} · Sumber: {sig.attachment_source ?? sig.source}
                </p>
                {sig.attachment_note ? <p className="mt-1 break-words text-xs text-muted-foreground">{sig.attachment_note}</p> : null}
              </div>
            ) : null}
          </div>
          <div className="grid w-full min-w-0 grid-cols-1 gap-3 text-sm sm:grid-cols-2 xl:w-auto xl:min-w-[300px]">
            <Info label="Sumber" value={sig.source} />
            <Info label="Waktu" value={new Date(sig.created_at).toLocaleString("id-ID")} />
            <Info label="Kategori Awal" value={sig.issue_category} />
            <Info label="Keyakinan Awal" value={`${Math.round(sig.source_confidence * 100)}%`} />
            <Info label="Vendor" value={sig.vendor_name} />
            <Info label="Lokasi" value={`${sig.school}, ${sig.region}`} />
          </div>
        </div>
      </SectionCard>

      {/* 2. Temukan Sinyal, Laporan, dan Bukti Terkait */}
      <SectionCard icon={FileSearch} title="2. Temukan Sinyal, Laporan, dan Bukti Terkait">
        <HelperPanel>
          Pencarian ini memakai sumber data demo/internal, bukan crawling real-time. Hasil adalah sinyal
          pra-verifikasi untuk membantu operator menilai keterkaitan — bukan pencocokan final.
        </HelperPanel>
        <p className="mt-3 rounded-lg border border-brand-500/25 bg-brand-500/10 p-3 text-xs text-brand-800 dark:text-brand-100">
          Keterkaitan antar-sinyal merupakan rekomendasi pra-verifikasi. Validasi lokasi, waktu, dan sumber
          tetap dilakukan oleh operator berwenang.
        </p>
        <button
          onClick={runSearch}
          disabled={searching}
          className="mt-4 inline-flex items-center gap-2 rounded-md bg-brand-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-600 disabled:opacity-60"
        >
          <FileSearch className="h-4 w-4" /> Cari Sinyal &amp; Bukti Terkait
        </button>

        {searching ? (
          <div className="mt-4 flex items-center gap-3">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-300 border-t-transparent" />
            <p className="text-sm text-muted-foreground">Mencari sinyal, laporan, dan bukti terkait…</p>
          </div>
        ) : null}

        {related ? (
          <div className="mt-5 space-y-6">
            <p className="text-xs text-muted-foreground">{related.source_note}</p>

            <CandidateGroup title="Kandidat kasus yang sudah ada" empty="Tidak ada kasus terkait ditemukan.">
              {related.case_candidates.map((c) => (
                <CandidateCard
                  key={c.case_id}
                  checked={selCases.has(c.case_id)}
                  onToggle={() => { toggle(setSelCases, c.case_id); if (decision === "merge") setTargetCase(c.case_id); }}
                  title={`${c.case_number} — ${c.title}`}
                  meta={`${c.vendor_name} · ${c.school}, ${c.region} · ${new Date(c.created_at).toLocaleDateString("id-ID")}`}
                  score={c.match_score}
                  reasons={c.reasons}
                  badges={[c.priority_label, c.issue_category]}
                />
              ))}
            </CandidateGroup>

            <CandidateGroup title="Sinyal/laporan belum terhubung" empty="Tidak ada sinyal terkait ditemukan.">
              {related.signal_candidates.map((s) => (
                <CandidateCard
                  key={s.id}
                  checked={selSignals.has(s.id)}
                  onToggle={() => toggle(setSelSignals, s.id)}
                  title={s.summary}
                  meta={`${s.source} · ${s.region} · ${new Date(s.created_at).toLocaleDateString("id-ID")}`}
                  score={s.match_score}
                  reasons={s.reasons}
                  badges={s.label ? [s.label] : []}
                  thumb={s.attachment_path}
                />
              ))}
            </CandidateGroup>

            <CandidateGroup title="Bukti yang mungkin relevan" empty="Tidak ada bukti terkait ditemukan.">
              {related.evidence_candidates.map((e) => (
                <CandidateCard
                  key={e.id}
                  checked={selEvidence.has(e.id)}
                  onToggle={() => toggle(setSelEvidence, e.id)}
                  title={e.title}
                  meta={`Keyakinan ${Math.round(e.confidence_score * 100)}% (pra-verifikasi)`}
                  score={e.match_score}
                  reasons={e.reasons}
                  badges={[e.type]}
                  thumb={e.type === "photo" ? e.file_path : undefined}
                />
              ))}
            </CandidateGroup>
          </div>
        ) : null}
      </SectionCard>

      {/* 3. Keputusan Keterkaitan */}
      <SectionCard icon={GitMerge} title="3. Keputusan Keterkaitan">
        <div className="space-y-3">
          <RadioRow name="decision" value="merge" current={decision} onChange={() => setDecision("merge")}
            label="Gabungkan ke kasus yang sudah ada" />
          {decision === "merge" ? (
            <div className="ml-7 rounded-lg border border-border bg-surface p-4">
              <label className="text-xs uppercase text-muted-foreground">Pilih kasus target</label>
              <select value={targetCase} onChange={(e) => setTargetCase(e.target.value)}
                className="mt-1 w-full rounded-md border border-border bg-surface-raised px-3 py-2 text-sm">
                <option value="">— pilih kasus —</option>
                {(related?.case_candidates ?? []).map((c) => (
                  <option key={c.case_id} value={c.case_id}>{c.case_number} — {c.title}</option>
                ))}
              </select>
              {targetCase ? (
                <p className="mt-3 break-words text-sm text-muted-foreground">
                  {(() => { const c = related?.case_candidates.find((x) => x.case_id === targetCase); return c ? `${c.case_number}: ${c.title} — ${c.vendor_name}, ${c.school}` : ""; })()}
                </p>
              ) : (
                <p className="mt-3 text-xs text-muted-foreground">Jalankan pencarian terkait dulu untuk melihat kandidat kasus.</p>
              )}
              <p className="mt-2 text-xs text-muted-foreground">Sinyal dan bukti/laporan terpilih akan ditautkan ke kasus ini.</p>
            </div>
          ) : null}

          <RadioRow name="decision" value="create" current={decision} onChange={() => setDecision("create")}
            label="Bentuk kasus baru" />
          {decision === "create" ? (
            <div className="ml-7 grid grid-cols-1 gap-3 rounded-lg border border-border bg-surface p-4 sm:grid-cols-2">
              <Field label="Judul kasus"><input value={ncTitle} onChange={(e) => setNcTitle(e.target.value)} className={inputCls} /></Field>
              <Field label="Kategori isu"><input value={ncIssue} onChange={(e) => setNcIssue(e.target.value)} placeholder="mis. porsi protein kurang" className={inputCls} /></Field>
              <Field label="Tipe kasus">
                <select value={ncCaseType} onChange={(e) => setNcCaseType(e.target.value)} className={inputCls}>
                  <option>Oversight</option><option>Keamanan pangan</option><option>Gizi & layanan</option><option>Kepatuhan vendor</option><option>Pengadaan</option>
                </select>
              </Field>
              <Field label="Subtipe (opsional)"><input value={ncCaseSubtype} onChange={(e) => setNcCaseSubtype(e.target.value)} placeholder="mis. kualitas porsi" className={inputCls} /></Field>
              <Field label="Provinsi">
                <select value={ncRegion} onChange={(e) => updateLocation(e.target.value, "", "")} className={inputCls}>
                  <option value="">Belum teridentifikasi</option>
                  {provinceItems.map((item) => <option key={item.province} value={item.province}>{item.province}</option>)}
                </select>
              </Field>
              <Field label="Kabupaten / Kota">
                <select value={ncDistrict} disabled={!ncRegion} onChange={(e) => updateLocation(ncRegion, e.target.value, "")} className={`${inputCls} disabled:opacity-60`}>
                  <option value="">Belum teridentifikasi</option>
                  {districtItems.map((item) => <option key={item.name} value={item.name}>{item.name}</option>)}
                </select>
              </Field>
              <Field label="Sekolah">
                {schoolManual ? (
                  <div className="space-y-2">
                    <input value={ncSchool} onChange={(e) => updateLocation(ncRegion, ncDistrict, e.target.value, true)} placeholder="Masukkan nama sekolah dari laporan" className={inputCls} />
                    <button type="button" onClick={() => updateLocation(ncRegion, ncDistrict, "")} className="text-xs text-brand-300 hover:text-brand-200">Pilih sekolah dari registry</button>
                  </div>
                ) : (
                  <select value={ncSchool} disabled={!ncRegion} onChange={(e) => e.target.value === MANUAL_SCHOOL_ID ? updateLocation(ncRegion, ncDistrict, "", true) : updateLocation(ncRegion, ncDistrict, e.target.value)} className={`${inputCls} disabled:opacity-60`}>
                    <option value="">Belum teridentifikasi</option>
                    {schoolItems.map((school) => <option key={school} value={school}>{school}</option>)}
                    <option value={MANUAL_SCHOOL_ID}>Sekolah belum terdaftar / masukkan dari laporan</option>
                  </select>
                )}
              </Field>
              <Field label="Vendor">
                <select value={ncVendor} onChange={(e) => { setNcVendor(e.target.value); setNcManualVendorName(""); setNcManualVendorNote(""); }} className={inputCls}>
                  <option value="">Belum teridentifikasi</option>
                  {assignmentOptions.vendors.map((vendor) => <option key={vendor.id} value={vendor.id}>{vendor.name}</option>)}
                  {ncRegion ? <option value={MANUAL_VENDOR_ID}>{assignmentOptions.manual_vendor.label}</option> : null}
                </select>
                {selectedVendor ? <p className="mt-2 rounded-md border border-brand-500/25 bg-brand-500/10 p-2 text-xs text-brand-800 dark:text-brand-100">Kandidat berdasarkan cakupan layanan wilayah. Konfirmasi operator tetap diperlukan.</p> : null}
                {assignmentOptions.vendor_message ? <p className="mt-2 text-xs text-muted-foreground">{assignmentOptions.vendor_message}</p> : null}
                {ncVendor === MANUAL_VENDOR_ID ? (
                  <div className="mt-2 grid gap-2">
                    <input value={ncManualVendorName} onChange={(e) => setNcManualVendorName(e.target.value)} placeholder="Nama penyedia dari laporan (wajib)" className={inputCls} />
                    <input value={ncManualVendorNote} onChange={(e) => setNcManualVendorNote(e.target.value)} placeholder="Sumber / catatan identifikasi (opsional)" className={inputCls} />
                  </div>
                ) : null}
              </Field>
              <div className="sm:col-span-2 space-y-2">
                <p className="text-xs text-muted-foreground">{assignmentOptions.governance_notice}</p>
                {locationNotice ? <p className="text-xs text-amber-700 dark:text-amber-200">{locationNotice}</p> : null}
                {assignmentLoading ? <p className="text-xs text-muted-foreground">Memuat kandidat wilayah…</p> : null}
              </div>
              <div className="sm:col-span-2">
                <Field label="Ringkasan kejadian"><textarea value={ncSummary} onChange={(e) => setNcSummary(e.target.value)} rows={3} className={inputCls} /></Field>
              </div>
              <div className="sm:col-span-2">
                <Field label="Ringkasan dampak"><textarea value={ncImpact} onChange={(e) => setNcImpact(e.target.value)} rows={2} placeholder="Dampak pada penerima layanan atau operasi yang perlu dipantau" className={inputCls} /></Field>
              </div>
              <Field label="Strategi penanganan">
                <select value={handlingStrategy} onChange={(e) => setHandlingStrategy(e.target.value as typeof handlingStrategy)} className={inputCls}>
                  <option value="direct">Tangani langsung (tanpa tiket)</option>
                  <option value="single_ticket">Satu workstream tiket</option>
                  <option value="multi_ticket">Beberapa workstream tiket</option>
                </select>
              </Field>
              <Field label="Relasi dengan kasus lain (opsional)"><input value={relatedCaseId} onChange={(e) => setRelatedCaseId(e.target.value)} placeholder="mis. case-001" className={inputCls} /></Field>
              {relatedCaseId ? <Field label="Jenis relasi"><select value={caseRelationship} onChange={(e) => setCaseRelationship(e.target.value)} className={inputCls}><option value="related">Terkait</option><option value="duplicate">Duplikat</option><option value="parent">Induk</option></select></Field> : null}
              <p className="text-xs text-muted-foreground sm:col-span-2">Sinyal dan bukti/laporan terpilih akan ditautkan ke kasus baru ini.</p>
              <p className="text-xs text-muted-foreground sm:col-span-2">Kasus langsung aktif sebagai “Open &amp; Monitored”. Strategi tiket hanya menentukan pola penanganan; tiket tidak dibuat otomatis.</p>
            </div>
          ) : null}

          <RadioRow name="decision" value="defer" current={decision} onChange={() => setDecision("defer")}
            label="Simpan sebagai perlu ditinjau nanti" />
          {decision === "defer" ? (
            <div className="ml-7 rounded-lg border border-border bg-surface p-4">
              <Field label="Alasan / catatan reviewer (wajib)">
                <textarea value={deferReason} onChange={(e) => setDeferReason(e.target.value)} rows={3} className={inputCls}
                  placeholder="mis. lokasi dan vendor belum jelas; menunggu klarifikasi awal" />
              </Field>
              <p className="mt-2 text-xs text-muted-foreground">Sinyal tetap tidak terhubung dan berstatus “Perlu Ditinjau”.</p>
            </div>
          ) : null}
        </div>
      </SectionCard>

      {/* 4. Penilaian Awal & Override */}
      {assessment ? (
        <SectionCard icon={ShieldAlert} title="4. Penilaian Awal Sistem (Pra-Verifikasi)">
          <HelperPanel>Nilai berikut adalah penilaian awal sistem, bukan keputusan final. Operator dapat menyesuaikan dengan justifikasi.</HelperPanel>
          <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <ScoreBar label="Dampak / keparahan" value={assessment.severity_score} />
              <ScoreBar label="Keyakinan" value={assessment.confidence_score} />
              <ScoreBar label="Kecukupan menu / gizi" value={assessment.nutrition_concern_score} />
              <ScoreBar label="Anomali biaya" value={assessment.cost_anomaly_score} />
              <ScoreBar label="Pola / kejadian berulang" value={assessment.anomaly_score} />
              <ScoreBar label="Skor prioritas awal" value={assessment.final_priority_score} />
            </div>
            <div className="min-w-0 rounded-lg border border-border bg-surface p-4">
              <p className="text-sm font-medium">Penyesuaian Operator</p>
              <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                <Field label="Prioritas">
                  <select value={ovPriority} onChange={(e) => setOvPriority(e.target.value)} className={inputCls}>
                    {["Rendah", "Sedang", "Tinggi", "Kritis"].map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                </Field>
                <Field label="Skor prioritas">
                  <input type="number" min={0} max={100} value={ovScore} onChange={(e) => setOvScore(Number(e.target.value))} className={inputCls} />
                </Field>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                <SideBySide label="Nilai sistem" a={assessment.priority_label} b={String(assessment.final_priority_score)} />
                <SideBySide label="Nilai operator" a={ovPriority} b={String(ovScore)} highlight={overrideAdjusted} />
              </div>
              <div className="mt-3">
                <Field label={`Alasan override${overrideAdjusted ? " (wajib)" : ""}`}>
                  <textarea value={ovReason} onChange={(e) => setOvReason(e.target.value)} rows={2} className={inputCls}
                    placeholder="Justifikasi bila prioritas/skor diubah dari nilai sistem" />
                </Field>
              </div>
              <p className="mt-2 break-words text-xs text-muted-foreground">{assessment.explanation}</p>
            </div>
          </div>
        </SectionCard>
      ) : null}

      {/* 5. Penugasan & Catatan Tindak Lanjut */}
      <SectionCard icon={UserCog} title="5. Penugasan & Catatan Tindak Lanjut">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Penanggung Jawab / Investigator">
            <select value={investigator} onChange={(e) => setInvestigator(e.target.value)} className={inputCls}>
              <option value="">— pilih —</option>
              {assignmentOptions.investigators.map((item) => <option key={item.id} value={item.name}>{item.name} · {item.role}</option>)}
            </select>
          </Field>
          <Field label="Unit Penanggung Jawab">
            <select value={unit} onChange={(e) => setUnit(e.target.value)} className={inputCls}>
              <option value="">— pilih —</option>
              {assignmentOptions.units.map((item) => <option key={item.id} value={item.name}>{item.name} · {item.role}</option>)}
            </select>
          </Field>
          <Field label="Pemilik sekunder (opsional)"><input value={secondaryOwner} onChange={(e) => setSecondaryOwner(e.target.value)} placeholder="Nama pemilik pendamping" className={inputCls} /></Field>
          <Field label="Watcher (opsional)"><input value={watchers} onChange={(e) => setWatchers(e.target.value)} placeholder="Nama 1, Nama 2" className={inputCls} /></Field>
          <Field label="Tingkat Urgensi">
            <select value={urgency} onChange={(e) => setUrgency(e.target.value)} className={inputCls}>
              {["Rendah", "Sedang", "Tinggi", "Kritis"].map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          </Field>
          <Field label="SLA Usulan (mengikuti urgensi)"><input value={sla} readOnly className={`${inputCls} opacity-70`} /></Field>
          <div className="sm:col-span-2">
            <Field label="Tindakan yang Direkomendasikan"><input value={recommended} onChange={(e) => setRecommended(e.target.value)} className={inputCls} /></Field>
          </div>
          <div className="sm:col-span-2">
            <Field label="Catatan Reviewer"><textarea value={reviewerNote} onChange={(e) => setReviewerNote(e.target.value)} rows={2} className={inputCls} /></Field>
          </div>
        </div>
        {sig.vendor_id ? null : (
          <p className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-800 dark:text-amber-200">
            Data sinyal sangat minim. Disarankan “Minta klarifikasi awal” atau “Kumpulkan bukti tambahan” sebelum verifikasi lapangan.
          </p>
        )}
      </SectionCard>

      {/* 6. Konfirmasi */}
      <SectionCard icon={ClipboardCheck} title="6. Konfirmasi">
        {result ? (
          <p className={result.ok
            ? "mb-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-800 dark:text-emerald-200"
            : "mb-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-800 dark:text-red-200"}>
            {result.text}
          </p>
        ) : null}
        <div className="flex flex-wrap items-center gap-3">
          <button onClick={submit} disabled={submitting}
            className="inline-flex items-center gap-2 rounded-md bg-brand-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-600 disabled:opacity-60">
            {submitting ? "Menyimpan…" : confirmLabel(decision, targetCase, related)}
          </button>
          <Link href="/intake" className="text-sm text-muted-foreground hover:text-foreground">Batal, kembali ke Kotak Masuk Sinyal</Link>
        </div>
      </SectionCard>

      <GovernanceNote compact />
    </div>
  );
}

const inputCls = "w-full rounded-md border border-border bg-surface-raised px-3 py-2 text-sm text-foreground";

function confirmLabel(decision: Decision, target: string, related: store.RelatedResult | null) {
  if (decision === "merge") {
    const c = related?.case_candidates.find((x) => x.case_id === target);
    return `Gabungkan ke ${c?.case_number ?? "Kasus MBG-xxx"}`;
  }
  if (decision === "create") return "Bentuk Kasus Baru";
  return "Simpan untuk Ditinjau Nanti";
}

function outcomeText(res: store.ReviewResult) {
  if (res.outcome === "merged") return `Sinyal digabungkan ke ${res.case_number}. Mengalihkan ke halaman kasus…`;
  if (res.outcome === "created") return `Kasus ${res.case_number} dibentuk. Mengalihkan ke halaman kasus…`;
  return "Sinyal disimpan sebagai perlu ditinjau. Kembali ke Kotak Masuk Sinyal…";
}

function SectionCard({ icon: Icon, title, children }: { icon: typeof Inbox; title: string; children: React.ReactNode }) {
  return (
    <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
      <h2 className="flex items-center gap-2 text-lg font-semibold">
        <Icon className="h-5 w-5 shrink-0 text-brand-300" />
        <span className="break-words">{title}</span>
      </h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function CandidateGroup({ title, empty, children }: { title: string; empty: string; children: React.ReactNode }) {
  const arr = Array.isArray(children) ? children : [children];
  const has = arr.some((c) => c);
  return (
    <div className="min-w-0">
      <h3 className="text-sm font-semibold uppercase text-muted-foreground">{title}</h3>
      {has ? (
        <div className="mt-3 grid grid-cols-1 gap-4 xl:grid-cols-2">{children}</div>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">{empty}</p>
      )}
    </div>
  );
}

function CandidateCard({
  checked, onToggle, title, meta, score, reasons, badges = [], thumb,
}: {
  checked: boolean; onToggle: () => void; title: string; meta: string; score: number;
  reasons: string[]; badges?: string[]; thumb?: string;
}) {
  return (
    <article className="min-w-0 rounded-lg border border-border bg-surface p-4">
      <div className="flex items-start gap-3">
        <input type="checkbox" checked={checked} onChange={onToggle} className="mt-1 h-4 w-4 shrink-0 accent-brand-500" aria-label={`Pilih ${title}`} />
        <div className="min-w-0 flex-1">
          <p className="break-words text-sm font-medium">{title}</p>
          <p className="mt-1 break-words text-xs text-muted-foreground">{meta}</p>
          {thumb ? (
            <div className="relative mt-2 aspect-video w-full max-w-[220px] overflow-hidden rounded-md border border-border">
              <Image src={thumb} alt={title} fill unoptimized className="object-cover" sizes="220px" />
            </div>
          ) : null}
          <div className="mt-2 flex flex-wrap gap-2">
            <EntityChip label={`Kecocokan ${score}`} tone="score" />
            {badges.map((b) => <StatusBadge key={b} label={b} />)}
          </div>
          <ul className="mt-2 space-y-0.5 text-xs text-muted-foreground">
            {reasons.map((r) => <li key={r} className="break-words">· {r}</li>)}
          </ul>
        </div>
      </div>
    </article>
  );
}

function RadioRow({ name, value, current, onChange, label }: { name: string; value: string; current: string; onChange: () => void; label: string }) {
  return (
    <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-border bg-surface p-3 text-sm">
      <input type="radio" name={name} value={value} checked={current === value} onChange={onChange} className="h-4 w-4 accent-brand-500" />
      <span className="font-medium">{label}</span>
    </label>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block min-w-0 text-xs">
      <span className="mb-1 block uppercase text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}

function SideBySide({ label, a, b, highlight }: { label: string; a: string; b: string; highlight?: boolean }) {
  return (
    <div className={`rounded-lg border p-3 ${highlight ? "border-brand-500/50 bg-brand-500/10" : "border-border bg-surface-raised"}`}>
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 break-words text-sm font-semibold">{a} · {b}</p>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg bg-surface p-3">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 break-words text-sm font-medium">{value}</p>
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="min-w-0 rounded-lg border border-border bg-surface p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="break-words text-sm font-medium">{label}</p>
        <p className="text-sm font-semibold">{value}</p>
      </div>
      <div className="mt-3 h-2 rounded-full bg-surface-overlay">
        <div className="h-2 rounded-full bg-brand-500" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
