"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  ClipboardList,
  FileText,
  History,
  ImageIcon,
  Link2Off,
  Radio,
  ShieldAlert,
  Ticket as TicketIcon,
} from "lucide-react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { api } from "@/lib/api";
import { getCase } from "@/lib/reviewStore";
import * as overlay from "@/lib/runtimeOverlay";
import { caseNumber } from "@/lib/utils";
import type { AuditTrailEvent, Evidence, OversightCase, Signal, Ticket } from "@/types/monitoring";

// Aksi status tiket (board: Baru, Sedang Ditinjau, Menunggu Klarifikasi Vendor, Verifikasi Lapangan, Selesai).
const TICKET_ACTIONS = [
  "Sedang Ditinjau",
  "Menunggu Klarifikasi Vendor",
  "Verifikasi Lapangan",
  "Selesai",
];

function fmt(dt: string) {
  return new Date(dt).toLocaleString("id-ID");
}

export default function CaseDetailPage() {
  const params = useParams<{ id: string }>();
  const fallback = getCase(params.id);
  const [item, setItem] = useState<OversightCase | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [actionNote, setActionNote] = useState<string | null>(null);
  const [unlinkTarget, setUnlinkTarget] = useState<Signal | null>(null);
  const [unlinkReason, setUnlinkReason] = useState("");
  const [unlinking, setUnlinking] = useState(false);

  useEffect(() => {
    async function load() {
      let apiCase: OversightCase | null = null;
      let usedApi = false;
      try {
        apiCase = await api.get<OversightCase>(`/cases/${params.id}`);
        usedApi = true;
      } catch {
        apiCase = null;
      }
      // Overlay runtime menang bila lebih lengkap (mis. evidence hasil merge yang
      // hilang dari API karena backend restart). Tanpa fallback ke kasus lain.
      const reconciled = overlay.reconcileCase(apiCase ?? fallback, params.id);
      if (reconciled) {
        setItem(reconciled);
        setSource(usedApi ? "api" : "fallback");
        if (!usedApi) setError("Backend tidak tersedia; menampilkan data demo lokal untuk kasus ini.");
      } else {
        setNotFound(true);
      }
      setLoading(false);
    }
    load();
  }, [fallback, params.id]);

  const sortedAudit = useMemo(
    () => [...(item?.audit_events ?? [])].sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp)),
    [item?.audit_events],
  );

  async function updateTicketStatus(status: string) {
    if (!item?.ticket) return;
    const now = new Date().toISOString();
    const optimisticTicket: Ticket = { ...item.ticket, status, updated_at: now };
    const auditEvent: AuditTrailEvent = {
      id: Date.now(),
      case_id: item.case_id,
      ticket_id: optimisticTicket.id,
      event_type: "status_changed",
      actor: "Operator Demo",
      role: "Operator Distrik",
      description: `Status tiket diubah menjadi ${status}.`,
      timestamp: now,
    };
    setItem({ ...item, status, ticket: optimisticTicket, audit_events: [auditEvent, ...item.audit_events] });
    setActionNote(`Tiket ${optimisticTicket.id} diperbarui menjadi "${status}". Peristiwa jejak audit dicatat.`);

    try {
      const result = await api.patch<{ ticket: Ticket; audit_event: AuditTrailEvent }, { status: string; note: string }>(
        `/tickets/${item.ticket.id}/status`,
        { status, note: `Aksi demo kasus ${item.case_id}: ${status}` },
      );
      setItem((cur) =>
        cur
          ? {
              ...cur,
              status,
              ticket: result.ticket,
              audit_events: [result.audit_event, ...cur.audit_events.filter((e) => e.id !== auditEvent.id)],
            }
          : cur,
      );
    } catch {
      setSource("fallback");
    }
  }

  async function confirmUnlink() {
    if (!item || !unlinkTarget) return;
    if (!unlinkReason.trim()) { setActionNote("Alasan pelepasan wajib diisi."); return; }
    setUnlinking(true);
    const sigId = unlinkTarget.id;
    try {
      const res = await api.post<{
        unlinked_evidence_ids: number[];
        audit_events: AuditTrailEvent[];
        case?: OversightCase | null;
      }, { reason: string }>(`/signals/${sigId}/unlink`, { reason: unlinkReason.trim() });

      // Overlay runtime: catat lepas relasi agar konsisten lintas refresh.
      overlay.recordUnlink(sigId, item.case_id, res.unlinked_evidence_ids ?? [], res.audit_events ?? [], res.case ?? undefined);

      const nextCase =
        res.case ??
        {
          ...item,
          signals: item.signals.filter((s) => s.id !== sigId),
          signals_count: Math.max(0, item.signals_count - 1),
          evidence: item.evidence.filter((e) => !(res.unlinked_evidence_ids ?? []).includes(e.id)),
          evidence_count: Math.max(0, item.evidence_count - (res.unlinked_evidence_ids ?? []).length),
          audit_events: [...(res.audit_events ?? []), ...item.audit_events],
        };
      setItem(nextCase);
      setActionNote(`Sinyal #${sigId} dilepas dari kasus. Sinyal kembali ke antrean “Perlu Ditinjau”. Peristiwa audit dicatat; aset tidak dihapus.`);
    } catch (e) {
      // Offline: putuskan relasi pada state lokal + overlay.
      const unlinkedEv = item.evidence.filter((ev) => ev.signal_id === sigId).map((ev) => ev.id);
      const auditEvents: AuditTrailEvent[] = [
        { id: Date.now(), case_id: item.case_id, ticket_id: "", event_type: "signal_unlinked", actor: "Operator Demo", role: "Operator Distrik", description: `Operator melepaskan sinyal #${sigId} dari ${item.case_number ?? caseNumber(item.case_id)}. Alasan: ${unlinkReason.trim()}. Data sumber dan aset tidak dihapus.`, timestamp: new Date().toISOString() },
        ...unlinkedEv.map((id) => ({ id: Date.now() + id, case_id: item.case_id, ticket_id: "", event_type: "evidence_unlinked", actor: "Operator Demo", role: "Operator Distrik", description: `Bukti #${id} ditandai 'Dilepas dari kasus'. Aset tidak dihapus.`, timestamp: new Date().toISOString() })),
      ];
      const nextCase: OversightCase = {
        ...item,
        signals: item.signals.filter((s) => s.id !== sigId),
        signals_count: Math.max(0, item.signals_count - 1),
        evidence: item.evidence.filter((ev) => !unlinkedEv.includes(ev.id)),
        evidence_count: Math.max(0, item.evidence_count - unlinkedEv.length),
        audit_events: [...auditEvents, ...item.audit_events],
      };
      overlay.recordUnlink(sigId, item.case_id, unlinkedEv, auditEvents, nextCase);
      setItem(nextCase);
      setSource("fallback");
      setActionNote(`Sinyal #${sigId} dilepas dari kasus (mode lokal). Sinyal kembali ke antrean “Perlu Ditinjau”. ${e instanceof Error ? "" : ""}`);
    } finally {
      setUnlinking(false);
      setUnlinkTarget(null);
      setUnlinkReason("");
    }
  }

  if (loading) return <LoadingState />;

  if (notFound || !item) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Kasus tidak ditemukan"
          description="Nomor kasus yang diminta tidak tersedia."
          breadcrumbs={[{ label: "Pusat Kendali", href: "/" }, { label: "Kasus", href: "/cases" }, { label: params.id }]}
        />
        <section className="rounded-xl border border-border bg-surface-raised p-6 text-sm text-muted-foreground">
          <p className="break-words">
            Kasus <span className="font-mono">{params.id}</span> tidak ada dalam sistem. Sistem tidak membuka kasus lain
            secara diam-diam. Kembali ke <Link href="/cases" className="text-brand-300 hover:underline">daftar kasus</Link>{" "}
            atau <Link href="/intake" className="text-brand-300 hover:underline">Kotak Masuk Sinyal</Link>.
          </p>
        </section>
      </div>
    );
  }

  const number = item.case_number ?? caseNumber(item.case_id);

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Kasus ${number}`}
        description={item.title}
        breadcrumbs={[{ label: "Pusat Kendali", href: "/" }, { label: "Kasus", href: "/cases" }, { label: number }]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      {actionNote ? (
        <p className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-800 dark:text-emerald-200">{actionNote}</p>
      ) : null}

      {/* 1. Ringkasan Kasus */}
      <SectionCard icon={FileText} title="1. Ringkasan Kasus">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap gap-2">
              <StatusBadge label={item.priority_label} />
              <StatusBadge label={item.status} />
              <EntityChip label={item.vendor_name} href={item.vendor_id === "vnd-unknown" ? undefined : `/vendors/${item.vendor_id}`} tone="vendor" />
              {item.ticket_id ? <EntityChip label={item.ticket_id} tone="ticket" /> : null}
            </div>
            <p className="mt-4 max-w-4xl break-words text-sm leading-6 text-muted-foreground">{item.summary}</p>
            <p className="mt-3 break-words text-sm leading-6 text-muted-foreground">
              <span className="font-medium text-foreground">Rekomendasi tindakan: </span>{item.recommended_action}
            </p>
            {item.vendor_source_note ? <p className="mt-2 break-words text-xs text-muted-foreground">Sumber identifikasi vendor: {item.vendor_source_note}</p> : null}
          </div>
          <div className="grid w-full min-w-0 grid-cols-1 gap-3 text-sm sm:grid-cols-2 xl:w-auto xl:min-w-[300px]">
            <Info label="Nomor Kasus" value={number} />
            <Info label="Prioritas" value={item.priority_label} />
            <Info label="Vendor" value={item.vendor_name} />
            <Info label="Lokasi" value={`${item.school}, ${item.district}, ${item.region}`} />
            <Info label="SLA" value={item.sla_status} />
            <Info label="Penanggung Jawab" value={item.assigned_investigator || "Belum ditetapkan"} />
            <Info label="Unit Penanggung Jawab" value={item.assigned_unit} />
          </div>
        </div>
      </SectionCard>

      {/* 2. Kronologi Aktivitas */}
      <SectionCard icon={History} title="2. Kronologi Aktivitas">
        <p className="mb-4 break-words text-sm text-muted-foreground">
          Alur kasus: sinyal masuk → kasus dibentuk → bukti ditambahkan → operator meninjau → risiko diperbarui →
          tiket dibuat → tindak lanjut → selesai.
        </p>
        <ol className="relative space-y-4 border-l border-border pl-5">
          {[...sortedAudit].reverse().map((event) => (
            <li key={event.id} className="min-w-0">
              <span className="absolute -left-[6.5px] mt-1.5 h-3 w-3 rounded-full border-2 border-brand-400 bg-surface" />
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge label={event.event_type.replaceAll("_", " ")} />
                <span className="text-xs text-muted-foreground">{fmt(event.timestamp)}</span>
              </div>
              <p className="mt-1 break-words text-sm text-muted-foreground">{event.description}</p>
              <p className="mt-0.5 break-words text-xs text-muted-foreground">{event.actor} · {event.role}</p>
            </li>
          ))}
        </ol>
      </SectionCard>

      {/* 3. Bukti & Verifikasi */}
      <SectionCard icon={ImageIcon} title="3. Bukti & Verifikasi">
        <HelperPanel>
          Foto dan dokumen di bawah adalah bukti pra-verifikasi yang perlu ditinjau operator. Skor keyakinan dan
          indikasi duplikat adalah sinyal awal — bukan bukti pelanggaran atau keputusan final.
        </HelperPanel>
        <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
          {item.evidence.map((ev) => (
            <EvidenceCard key={ev.id} ev={ev} />
          ))}
        </div>

        {/* Signal terhubung + aksi sekunder Lepaskan dari Kasus */}
        {item.signals.length ? (
          <div className="mt-6">
            <h3 className="flex items-center gap-2 text-sm font-semibold uppercase text-muted-foreground">
              <Radio className="h-4 w-4" /> Signal Terhubung
            </h3>
            <p className="mt-2 break-words text-xs text-muted-foreground">
              Signal terhubung ke kasus ini sebagai sinyal pendukung. Keterkaitan tetap memerlukan verifikasi operator.
            </p>
            <div className="mt-3 space-y-2">
              {item.signals.map((sig) => (
                <div key={sig.id} className="flex flex-col gap-2 rounded-lg border border-border bg-surface p-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <p className="break-words text-sm font-medium">{sig.summary}</p>
                    <p className="mt-0.5 break-words text-xs text-muted-foreground">#{sig.id} · {sig.source} · {sig.region}</p>
                  </div>
                  <button
                    onClick={() => { setUnlinkTarget(sig); setUnlinkReason(""); }}
                    className="inline-flex shrink-0 items-center gap-1.5 self-start rounded-md border border-border px-2.5 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:border-red-500/40 hover:bg-red-500/10 hover:text-red-700 dark:hover:text-red-300 sm:self-auto"
                  >
                    <Link2Off className="h-3.5 w-3.5" /> Lepaskan dari Kasus
                  </button>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </SectionCard>

      {/* 4. Penilaian Risiko */}
      <SectionCard icon={ShieldAlert} title="4. Penilaian Risiko">
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:col-span-2">
            <ScoreBar label="Severity" value={item.score.severity_score} />
            <ScoreBar label="Confidence (keyakinan)" value={item.score.confidence_score} />
            <ScoreBar label="Kecukupan menu / gizi" value={item.score.nutrition_concern_score} />
            <ScoreBar label="Anomali biaya" value={item.score.cost_anomaly_score} />
            <ScoreBar label="Pola / kejadian berulang" value={item.score.anomaly_score} />
            <ScoreBar label="Skor akhir" value={item.score.final_priority_score} />
          </div>
          <div className="min-w-0 rounded-lg border border-border bg-surface p-4">
            <StatusBadge label={item.priority_label} />
            <p className="mt-3 break-words text-sm leading-6 text-muted-foreground">{item.risk_explanation}</p>
          </div>
        </div>
      </SectionCard>

      {/* 5. Tindakan / Tiket */}
      <SectionCard icon={TicketIcon} title="5. Tindakan / Tiket">
        {item.ticket ? (
          <>
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div className="min-w-0">
                <h3 className="break-words text-base font-semibold">{item.ticket.title}</h3>
                <p className="mt-1 break-words text-sm text-muted-foreground">{item.ticket.id} · {item.ticket.assigned_unit}</p>
              </div>
              <StatusBadge label={item.ticket.status} />
            </div>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Info label="SLA" value={item.ticket.sla} />
              <Info label="Tingkat Eskalasi" value={item.ticket.escalation_level} />
              <Info label="Bukti Tertaut" value={`${item.ticket.linked_evidence_ids.length} bukti`} />
              <Info label="Pembaruan Terakhir" value={fmt(item.ticket.updated_at)} />
            </div>
            <p className="mt-4 break-words text-sm text-muted-foreground">
              <span className="font-medium text-foreground">Tindakan yang direkomendasikan: </span>{item.ticket.recommended_action}
            </p>
            <p className="mt-5 text-sm font-medium">Ubah status tiket</p>
            <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:flex lg:flex-wrap">
              {TICKET_ACTIONS.map((status) => (
                <button
                  key={status}
                  onClick={() => updateTicketStatus(status)}
                  className="rounded-md border border-border px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-surface hover:text-foreground"
                >
                  {status}
                </button>
              ))}
            </div>
          </>
        ) : (
          <HelperPanel>Belum ada tiket tindak lanjut untuk kasus ini.</HelperPanel>
        )}
      </SectionCard>

      {/* 6. Laporan Kasus */}
      <SectionCard icon={ClipboardList} title="6. Laporan Kasus">
        <div className="space-y-4 text-sm leading-6 text-muted-foreground">
          <ReportBlock title="Fakta yang masuk">{item.what_happened}</ReportBlock>
          <ReportBlock title="Mengapa ini penting">{item.why_it_matters}</ReportBlock>
          <ReportBlock title="Bukti yang ditinjau">
            {`${item.evidence.length} bukti pra-verifikasi terkait ${item.vendor_name} (foto, dokumen, dan metadata) — seluruhnya masih memerlukan peninjauan operator.`}
          </ReportBlock>
          <ReportBlock title="Penilaian risiko">
            {`Skor akhir ${item.score.final_priority_score} (${item.priority_label}). ${item.risk_explanation}`}
          </ReportBlock>
          <ReportBlock title="Tindakan operator">
            {item.ticket
              ? `Tiket ${item.ticket.id} berstatus "${item.ticket.status}" pada unit ${item.ticket.assigned_unit} (SLA ${item.ticket.sla}).`
              : "Belum ada tiket tindak lanjut."}
          </ReportBlock>
          <p className="rounded-lg border border-brand-500/25 bg-brand-500/10 p-3 text-brand-800 dark:text-brand-100">
            Catatan: ringkasan ini merupakan sinyal pra-verifikasi. Hasil masih memerlukan verifikasi lapangan dan
            keputusan dari otoritas berwenang.
          </p>
        </div>
      </SectionCard>

      {/* 7. Jejak Audit */}
      <SectionCard icon={History} title="7. Jejak Audit">
        <div className="space-y-3">
          {sortedAudit.map((event) => (
            <div key={event.id} className="grid min-w-0 gap-4 rounded-lg border border-border bg-surface p-4 lg:grid-cols-[170px_minmax(0,1fr)_180px]">
              <div>
                <p className="font-mono text-xs text-brand-300">{caseNumber(event.case_id)}</p>
                <p className="mt-1 text-xs text-muted-foreground">{fmt(event.timestamp)}</p>
              </div>
              <div>
                <StatusBadge label={event.event_type.replaceAll("_", " ")} />
                <p className="mt-3 break-words text-sm text-muted-foreground">{event.description}</p>
              </div>
              <div className="min-w-0 text-sm">
                <p className="break-words font-medium">{event.actor}</p>
                <p className="break-words text-muted-foreground">{event.role}</p>
                <p className="break-words font-mono text-xs text-muted-foreground">{event.ticket_id}</p>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile label="Sinyal Terhubung" value={String(item.signals_count)} />
        <MetricTile label="Bukti" value={String(item.evidence_count)} />
        <MetricTile label="Skor Akhir" value={String(item.score.final_priority_score)} detail={item.priority_label} />
        <MetricTile label="Peristiwa Audit" value={String(item.audit_events.length)} />
      </div>

      {/* Dialog konfirmasi Lepaskan dari Kasus */}
      {unlinkTarget ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-md rounded-xl border border-border bg-surface-raised p-5 shadow-xl">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <Link2Off className="h-5 w-5 text-red-500" /> Lepaskan Sinyal dari Kasus
            </h2>
            <p className="mt-3 break-words text-sm text-muted-foreground">
              Anda akan melepaskan sinyal <span className="font-medium">#{unlinkTarget.id}</span> dari{" "}
              {item.case_number ?? caseNumber(item.case_id)}. Melepaskan signal tidak menghapus data sumber; tindakan ini
              hanya mengakhiri hubungan signal dengan kasus dan dicatat pada jejak audit.
            </p>
            <label className="mt-4 block text-xs">
              <span className="mb-1 block uppercase text-muted-foreground">Alasan pelepasan (wajib)</span>
              <textarea
                value={unlinkReason}
                onChange={(e) => setUnlinkReason(e.target.value)}
                rows={3}
                className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground"
                placeholder="mis. lokasi/waktu belum terkonfirmasi; sinyal perlu klarifikasi awal"
              />
            </label>
            <div className="mt-4 flex flex-wrap justify-end gap-2">
              <button
                onClick={() => { setUnlinkTarget(null); setUnlinkReason(""); }}
                disabled={unlinking}
                className="rounded-md border border-border px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-surface disabled:opacity-60"
              >
                Batal
              </button>
              <button
                onClick={confirmUnlink}
                disabled={unlinking || !unlinkReason.trim()}
                className="rounded-md bg-red-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 disabled:opacity-60"
              >
                {unlinking ? "Melepaskan…" : "Lepaskan dari Kasus"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function SectionCard({
  icon: Icon,
  title,
  children,
}: {
  icon: typeof FileText;
  title: string;
  children: React.ReactNode;
}) {
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

function EvidenceCard({ ev }: { ev: Evidence }) {
  const isPhoto = ev.type === "photo" && ev.file_path;
  const typeLabel = ev.source?.toLowerCase().includes("media sosial")
    ? "Foto / Lampiran media sosial"
    : ev.type === "photo" ? "Foto" : ev.type;
  return (
    <article className="min-w-0 rounded-lg border border-border bg-surface p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="break-words font-medium">{ev.title}</p>
          <p className="mt-1 break-words text-xs text-muted-foreground">{ev.linked_entity} · {fmt(ev.created_at)}</p>
        </div>
        <StatusBadge label={typeLabel} />
      </div>
      {isPhoto ? (
        <div className="relative mt-3 aspect-video w-full overflow-hidden rounded-md border border-border bg-surface-overlay">
          <Image src={ev.file_path!} alt={ev.title} fill unoptimized className="object-cover" sizes="(max-width: 768px) 100vw, 400px" />
        </div>
      ) : null}
      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Info label="Keyakinan (pra-verifikasi)" value={`${Math.round(ev.confidence_score * 100)}%`} />
        <Info label="Kecocokan Gambar/Teks" value={ev.image_text_match_score == null ? "-" : `${Math.round(ev.image_text_match_score * 100)}%`} />
        <Info label="Indikasi Duplikat" value={ev.duplicate_score == null ? "-" : `${Math.round(ev.duplicate_score * 100)}%`} />
      </div>
      {ev.ocr_result ? (
        <p className="mt-3 break-words rounded-lg bg-surface-overlay p-3 text-sm text-muted-foreground">{ev.ocr_result}</p>
      ) : null}
      <p className="mt-3 break-words text-sm text-muted-foreground">{ev.reviewer_note}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <StatusBadge label={ev.review_status ?? "Perlu Ditinjau"} />
        {ev.source ? <EntityChip label={`Sumber: ${ev.source}`} tone="evidence" /> : null}
      </div>
    </article>
  );
}

function ReportBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <p className="break-words">
      <span className="font-medium text-foreground">{title}: </span>{children}
    </p>
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
