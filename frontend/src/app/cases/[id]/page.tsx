"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  ClipboardList,
  Activity,
  ChevronDown,
  CircleAlert,
  FileText,
  History,
  ImageIcon,
  Link2Off,
  Radio,
  ShieldAlert,
  Ticket as TicketIcon,
  UserCog,
  Pencil,
  Plus,
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

// Aksi status tiket. Backend memvalidasi transisi; tombol yang tidak valid
// dari status sekarang disembunyikan lewat TICKET_TRANSITIONS.
const TICKET_ACTIONS = [
  "Sedang Ditinjau",
  "Menunggu Klarifikasi Vendor",
  "Verifikasi Lapangan",
  "Ditahan / On Hold",
  "Selesai",
  "Ditutup",
];

// Mirror of app/ticketing.py TRANSITIONS — keeps the UI from offering a move
// the backend will reject with a 422.
const TICKET_TRANSITIONS: Record<string, string[]> = {
  "Baru": ["Sedang Ditinjau", "Verifikasi Lapangan", "Menunggu Klarifikasi Vendor", "Ditahan / On Hold", "Dibatalkan"],
  "Sedang Ditinjau": ["Verifikasi Lapangan", "Menunggu Klarifikasi Vendor", "Ditahan / On Hold", "Selesai", "Dibatalkan"],
  "Verifikasi Lapangan": ["Sedang Ditinjau", "Menunggu Klarifikasi Vendor", "Ditahan / On Hold", "Selesai", "Dibatalkan"],
  "Menunggu Klarifikasi Vendor": ["Sedang Ditinjau", "Verifikasi Lapangan", "Ditahan / On Hold", "Selesai", "Dibatalkan"],
  "Ditahan / On Hold": ["Sedang Ditinjau", "Verifikasi Lapangan", "Menunggu Klarifikasi Vendor", "Dibatalkan"],
  "Selesai": ["Ditutup", "Sedang Ditinjau"],
  "Ditutup": ["Sedang Ditinjau"],
  "Dibatalkan": [],
};

const SEVERITIES = ["Kritis", "Tinggi", "Sedang", "Rendah"];
const IMPACTS = ["Luas", "Sedang", "Terbatas"];
const URGENCIES = ["Segera", "Normal", "Terjadwal"];
const SLA_POLICIES = [
  { code: "P1", label: "P1 — 4 jam (Kritis)" },
  { code: "P2", label: "P2 — 24 jam (Tinggi)" },
  { code: "P3", label: "P3 — 48 jam (Sedang)" },
  { code: "P4", label: "P4 — 72 jam (Rendah)" },
];

const EMPTY_TICKET_FORM = {
  title: "", description: "", severity: "", impact: "", urgency: "",
  sla_policy: "", due_at: "", assignee: "", assignment_group: "",
  workstream: "", category: "", notes: "",
};

const CASE_STATUSES = [
  "Open & Monitored", "Assessing", "In Handling", "Pending / Blocked", "Escalated",
  "Resolved – Pending Verification", "Closed", "Reopened", "Merged / Invalid",
];

const SLA_STATE_LABEL: Record<string, string> = {
  on_track: "On track", at_risk: "Berisiko", overdue: "Terlambat",
  paused: "SLA dijeda", met: "Selesai dalam SLA", breached: "Melewati SLA",
  unknown: "SLA tidak diketahui",
};

function fmt(dt: string) {
  return new Date(dt).toLocaleString("id-ID");
}

const OWNER_FIELDS = ["primary_owner", "handling_team", "secondary_owner"] as const;

/** Pilih hanya field kepemilikan dari payload; "" berarti dikosongkan (null). */
function ownerFields(extra: Record<string, string>): Partial<Record<(typeof OWNER_FIELDS)[number], string | null>> {
  const out: Partial<Record<(typeof OWNER_FIELDS)[number], string | null>> = {};
  for (const key of OWNER_FIELDS) {
    if (key in extra) out[key] = extra[key].trim() || null;
  }
  return out;
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
  const [caseStatus, setCaseStatus] = useState("");
  const [progressNote, setProgressNote] = useState("");
  const [resolutionSummary, setResolutionSummary] = useState("");
  const [newTicket, setNewTicket] = useState({ ...EMPTY_TICKET_FORM });
  const [newBlocker, setNewBlocker] = useState("");
  const [editingOwners, setEditingOwners] = useState(false);
  const [ownerDraft, setOwnerDraft] = useState({ primary_owner: "", handling_team: "", secondary_owner: "" });
  const [savingOwners, setSavingOwners] = useState(false);

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
        setCaseStatus(reconciled.status);
        setResolutionSummary(reconciled.resolution_summary ?? "");
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

  const childTickets = useMemo(() => item?.tickets ?? (item?.ticket ? [item.ticket] : []), [item]);

  // sortedAudit is newest-first, so [0] is the latest activity.
  const lastEvent = sortedAudit[0];

  async function updateTicketStatus(ticketToUpdate: Ticket, status: string) {
    if (!item) return;
    const now = new Date().toISOString();
    const optimisticTicket: Ticket = { ...ticketToUpdate, status, updated_at: now };
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
    setItem({ ...item, ticket: item.ticket?.id === optimisticTicket.id ? optimisticTicket : item.ticket, tickets: childTickets.map((ticket) => ticket.id === optimisticTicket.id ? optimisticTicket : ticket), audit_events: [auditEvent, ...item.audit_events] });
    setActionNote(`Workstream ${optimisticTicket.id} diperbarui menjadi "${status}". Status kasus tetap ${item.status}.`);

    try {
      const result = await api.patch<{ ticket: Ticket; audit_event: AuditTrailEvent }, { status: string; note: string }>(
        `/tickets/${ticketToUpdate.id}/status`,
        { status, note: `Aksi demo kasus ${item.case_id}: ${status}` },
      );
      setItem((cur) => {
        if (!cur) return cur;
        const next = {
          ...cur,
          ticket: cur.ticket?.id === result.ticket.id ? result.ticket : cur.ticket,
          tickets: (cur.tickets ?? (cur.ticket ? [cur.ticket] : [])).map((ticket) => ticket.id === result.ticket.id ? result.ticket : ticket),
          audit_events: [result.audit_event, ...cur.audit_events.filter((e) => e.id !== auditEvent.id)],
          updated_at: result.ticket.updated_at ?? now,
        };
        // Without this the overlay keeps a snapshot holding the *old* ticket
        // status, and reconcileCase can serve it back on the next visit —
        // which is why the case page used to disagree with the ticket board.
        overlay.recordCase(next);
        return next;
      });
    } catch {
      setSource("fallback");
      // Offline: the optimistic ticket is all we have, so persist it too rather
      // than leaving the overlay holding a pre-change snapshot.
      overlay.recordCase({
        ...item,
        ticket: item.ticket?.id === optimisticTicket.id ? optimisticTicket : item.ticket,
        tickets: childTickets.map((t) => (t.id === optimisticTicket.id ? optimisticTicket : t)),
        audit_events: [auditEvent, ...item.audit_events],
        updated_at: now,
      });
    }
  }

  async function saveCaseUpdate(extra: Record<string, string> = {}, successNote?: string) {
    if (!item) return;
    if (caseStatus === "Closed" && !resolutionSummary.trim()) {
      setActionNote("Kasus hanya dapat ditutup setelah ringkasan resolusi terverifikasi diisi.");
      return;
    }
    const payload = { status: caseStatus, progress_note: progressNote || undefined, resolution_summary: resolutionSummary || undefined, ...extra };
    try {
      const result = await api.patch<{ case: OversightCase }, typeof payload>(`/cases/${item.case_id}`, payload);
      setItem(result.case);
      overlay.recordCase(result.case);
      setCaseStatus(result.case.status);
      setProgressNote("");
      setActionNote(successNote ?? "Progres kasus diperbarui dan tercatat di timeline.");
    } catch {
      const now = new Date().toISOString();
      const event: AuditTrailEvent = { id: Date.now(), case_id: item.case_id, ticket_id: "", event_type: "handling_update", actor: "Operator Demo", role: "Operator Distrik", description: progressNote || successNote || "Pembaruan penanganan kasus (mode lokal).", timestamp: now };
      // `extra` carries the ownership/blocker fields; applying it here (not just
      // status) is what makes an offline edit survive a refresh, because the
      // overlay snapshot below is what the page reads back.
      const owners = ownerFields(extra);
      const blockers = extra.blocker && !(item.blockers ?? []).includes(extra.blocker)
        ? [...(item.blockers ?? []), extra.blocker]
        : item.blockers;
      const nextCase: OversightCase = {
        ...item, ...owners, blockers,
        status: caseStatus,
        resolution_summary: resolutionSummary || item.resolution_summary,
        // Legacy aliases stay in sync with the case-centric fields, mirroring
        // what the backend does on the same PATCH.
        assigned_investigator: "primary_owner" in owners ? owners.primary_owner ?? null : item.assigned_investigator,
        assigned_unit: "handling_team" in owners ? owners.handling_team ?? "" : item.assigned_unit,
        audit_events: [event, ...item.audit_events],
        updated_at: now,
      };
      setItem(nextCase);
      overlay.recordCase(nextCase);
      setSource("fallback");
      setProgressNote("");
      setActionNote(successNote ? `${successNote} (mode lokal).` : "Progres kasus disimpan pada mode lokal.");
    }
  }

  function startOwnerEdit() {
    if (!item) return;
    setOwnerDraft({
      primary_owner: item.primary_owner ?? item.assigned_investigator ?? "",
      handling_team: item.handling_team ?? item.assigned_unit ?? "",
      secondary_owner: item.secondary_owner ?? "",
    });
    setEditingOwners(true);
  }

  async function saveOwners() {
    setSavingOwners(true);
    // Empty strings are sent deliberately: the backend reads them as an
    // explicit "clear this owner" rather than skipping the field.
    await saveCaseUpdate(
      {
        primary_owner: ownerDraft.primary_owner.trim(),
        handling_team: ownerDraft.handling_team.trim(),
        secondary_owner: ownerDraft.secondary_owner.trim(),
      },
      "Kepemilikan kasus diperbarui dan tercatat di jejak audit.",
    );
    setSavingOwners(false);
    setEditingOwners(false);
  }

  async function createChildTicket() {
    if (!item || !newTicket.title.trim()) return;
    // Blank fields are omitted, not sent as "": the backend applies its
    // documented inheritance rules and reports which ones it used.
    const payload = Object.fromEntries(
      Object.entries({
        title: newTicket.title.trim(),
        description: newTicket.description.trim() || undefined,
        severity: newTicket.severity || undefined,
        impact: newTicket.impact || undefined,
        urgency: newTicket.urgency || undefined,
        sla_policy: newTicket.sla_policy || undefined,
        due_at: newTicket.due_at ? new Date(newTicket.due_at).toISOString() : undefined,
        assignee: newTicket.assignee.trim() || undefined,
        assignment_group: newTicket.assignment_group.trim() || undefined,
        workstream: newTicket.workstream.trim() || undefined,
        category: newTicket.category.trim() || undefined,
        notes: newTicket.notes.trim() || undefined,
      }).filter(([, v]) => v !== undefined),
    );
    try {
      const result = await api.post<
        { case: OversightCase; ticket: Ticket; applied_rules: Record<string, string> },
        typeof payload
      >(`/cases/${item.case_id}/tickets`, payload);
      setItem(result.case);
      overlay.recordCase(result.case);
      setNewTicket({ ...EMPTY_TICKET_FORM });
      setActionNote(
        `Tiket ${result.ticket.id} dibuat — keparahan ${result.ticket.severity} (${result.applied_rules.severity}), ` +
          `SLA ${result.ticket.sla} (${result.applied_rules.sla}), pemilik ${result.ticket.assignee ?? "belum ditetapkan"} ` +
          `· ${result.ticket.assignment_group} (${result.applied_rules.assignment}).`,
      );
    } catch {
      setActionNote("Tiket anak memerlukan backend aktif. Kasus tetap dapat ditangani langsung tanpa tiket.");
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
      {/* Judul kasus (bukan nomornya) yang dominan: nomor kasus turun jadi
          eyebrow supaya pembaca langsung menangkap kasus ini tentang apa. */}
      <PageHeader
        title={item.title}
        eyebrow={number}
        description={item.impact_summary || item.summary}
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
              <StatusBadge label={item.handling_strategy === "direct" ? "Tangani langsung" : item.handling_strategy === "multi_ticket" ? "Multi-workstream" : "Single workstream"} />
              <EntityChip label={item.vendor_name} href={item.vendor_id === "vnd-unknown" ? undefined : `/vendors/${item.vendor_id}`} tone="vendor" />
              {/* Semua tiket anak, bukan hanya tickets[0] (ticket_id). Di atas 3
                  tiket diringkas jadi "+N" agar baris chip tidak meledak. */}
              {childTickets.slice(0, 3).map((ticket) => <EntityChip key={ticket.id} label={ticket.id} tone="ticket" />)}
              {childTickets.length > 3 ? <EntityChip label={`+${childTickets.length - 3} tiket`} tone="ticket" /> : null}
            </div>
            <h3 className="mt-4 max-w-[68ch] break-words text-base font-semibold leading-snug text-foreground sm:text-lg">
              {item.title}
            </h3>
            {item.impact_summary && item.impact_summary !== item.summary ? (
              <p className="mt-2 max-w-[68ch] break-words text-sm leading-6 text-foreground/90">{item.impact_summary}</p>
            ) : null}
            <p className="mt-3 max-w-[68ch] break-words text-sm leading-6 text-muted-foreground">{item.summary}</p>
            <p className="mt-4 max-w-[68ch] break-words rounded-lg border border-border bg-surface p-3 text-sm leading-6 text-muted-foreground">
              <span className="font-medium text-foreground">Rekomendasi tindakan: </span>{item.recommended_action}
            </p>
            {item.vendor_source_note ? <p className="mt-2 break-words text-xs text-muted-foreground">Sumber identifikasi vendor: {item.vendor_source_note}</p> : null}
          </div>
          <div className="grid w-full min-w-0 grid-cols-1 gap-3 text-sm sm:grid-cols-2 xl:w-auto xl:min-w-[300px]">
            <Info label="Nomor Kasus" value={number} />
            <Info label="Prioritas" value={item.priority_label} />
            <Info label="Tipe kasus" value={item.case_type ?? "Oversight"} />
            <Info label="Vendor" value={item.vendor_name} />
            <Info label="Lokasi" value={`${item.school}, ${item.district}, ${item.region}`} />
            <Info label="SLA" value={item.sla_status} />
            <Info label="Pemilik Utama" value={item.primary_owner || item.assigned_investigator || "Belum ditetapkan"} />
            <Info label="Tim / Unit Penanggung Jawab" value={item.handling_team || item.assigned_unit || "Belum ditetapkan"} />
            <Info label="Usia kasus" value={`${Math.max(0, Math.floor((Date.now() - Date.parse(item.created_at)) / 86_400_000))} hari`} />
          </div>
        </div>
      </SectionCard>

      {/* 2. Workspace Penanganan Kasus */}
      <SectionCard icon={Activity} title="2. Workspace Penanganan Kasus">
        <p className="mb-4 text-sm text-muted-foreground">Kasus adalah sumber kebenaran penanganan. Perbarui progres dan lifecycle di sini; status tiket anak tidak mengubah status kasus secara otomatis.</p>
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
          <label className="text-xs"><span className="mb-1 block uppercase text-muted-foreground">Status kasus</span><select value={caseStatus} onChange={(e) => setCaseStatus(e.target.value)} className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm">{CASE_STATUSES.map((status) => <option key={status}>{status}</option>)}</select></label>
          <label className="text-xs lg:col-span-2"><span className="mb-1 block uppercase text-muted-foreground">Pembaruan penanganan</span><input value={progressNote} onChange={(e) => setProgressNote(e.target.value)} placeholder="mis. klarifikasi vendor diterima; verifikasi lapangan dijadwalkan" className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm" /></label>
          {(caseStatus === "Resolved – Pending Verification" || caseStatus === "Closed") ? <label className="text-xs lg:col-span-3"><span className="mb-1 block uppercase text-muted-foreground">Ringkasan resolusi terverifikasi {caseStatus === "Closed" ? "(wajib)" : ""}</span><textarea value={resolutionSummary} onChange={(e) => setResolutionSummary(e.target.value)} rows={2} className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm" placeholder="Bukti resolusi, hasil verifikasi, dan tindakan pencegahan" /></label> : null}
        </div>
        <button onClick={() => void saveCaseUpdate()} className="mt-3 rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">Simpan progres kasus</button>
        <div className="mt-5 grid grid-cols-1 gap-3 lg:grid-cols-2">
          <div className="rounded-lg border border-border bg-surface p-4">
            <div className="flex items-start justify-between gap-3">
              <p className="flex items-center gap-2 text-sm font-medium"><UserCog className="h-4 w-4" /> Kepemilikan</p>
              {editingOwners ? null : (
                <button onClick={startOwnerEdit} className="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-xs font-medium text-muted-foreground hover:bg-surface-raised hover:text-foreground">
                  <Pencil className="h-3.5 w-3.5" /> Ubah
                </button>
              )}
            </div>
            {editingOwners ? (
              <div className="mt-3 space-y-3">
                <OwnerField label="Pemilik utama" value={ownerDraft.primary_owner} onChange={(v) => setOwnerDraft({ ...ownerDraft, primary_owner: v })} placeholder="Nama penanggung jawab kasus" />
                <OwnerField label="Tim / unit penanggung jawab" value={ownerDraft.handling_team} onChange={(v) => setOwnerDraft({ ...ownerDraft, handling_team: v })} placeholder="mis. Unit Pengawasan Vendor MBG" />
                <OwnerField label="Pemilik sekunder (opsional)" value={ownerDraft.secondary_owner} onChange={(v) => setOwnerDraft({ ...ownerDraft, secondary_owner: v })} placeholder="Nama pemilik pendamping" />
                <p className="text-xs text-muted-foreground">Kolom yang dikosongkan berarti kepemilikan dilepas dan ditandai “Belum ditetapkan”. Tiket anak yang dibuat setelahnya mewarisi nilai baru ini; tiket yang sudah ada tidak ikut berubah.</p>
                <div className="flex flex-wrap gap-2">
                  <button onClick={() => void saveOwners()} disabled={savingOwners} className="rounded-md bg-brand-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-400 disabled:opacity-60">{savingOwners ? "Menyimpan…" : "Simpan kepemilikan"}</button>
                  <button onClick={() => setEditingOwners(false)} disabled={savingOwners} className="rounded-md border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-surface-raised disabled:opacity-60">Batal</button>
                </div>
              </div>
            ) : (
              <dl className="mt-3 space-y-2">
                <OwnerRow label="Pemilik utama" value={item.primary_owner ?? item.assigned_investigator} />
                <OwnerRow label="Tim / unit" value={item.handling_team ?? item.assigned_unit} />
                <OwnerRow label="Pemilik sekunder" value={item.secondary_owner} />
              </dl>
            )}
          </div>
          <div className="rounded-lg border border-border bg-surface p-4"><p className="flex items-center gap-2 text-sm font-medium"><CircleAlert className="h-4 w-4" /> Hambatan & dependensi</p>{(item.blockers ?? []).length ? <ul className="mt-2 space-y-1 text-sm text-muted-foreground">{item.blockers!.map((blocker) => <li key={blocker}>• {blocker}</li>)}</ul> : <p className="mt-2 text-sm text-muted-foreground">Tidak ada hambatan aktif.</p>}<div className="mt-3 flex gap-2"><input value={newBlocker} onChange={(e) => setNewBlocker(e.target.value)} placeholder="Tambahkan hambatan" className="min-w-0 flex-1 rounded-md border border-border bg-surface-raised px-2 py-1.5 text-xs" /><button onClick={() => { if (newBlocker.trim()) { void saveCaseUpdate({ blocker: newBlocker.trim() }); setNewBlocker(""); } }} className="rounded-md border border-border px-2 py-1.5 text-xs">Tambah</button></div></div>
        </div>
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

      {/* 5. Workstream / Tiket Anak */}
      <SectionCard icon={TicketIcon} title="5. Workstream / Tiket Anak">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
          <Info label="Total" value={String(item.ticket_summary?.total ?? childTickets.length)} />
          <Info label="Dikerjakan" value={String(item.ticket_summary?.in_progress ?? 0)} />
          <Info label="Menunggu" value={String(item.ticket_summary?.waiting ?? 0)} />
          <Info label="Selesai" value={String(item.ticket_summary?.completed ?? 0)} />
          <Info label="On track" value={String(item.ticket_summary?.on_track ?? 0)} />
          <Info label="Berisiko" value={String(item.ticket_summary?.at_risk ?? 0)} />
          <Info label="Terlambat" value={String(item.ticket_summary?.overdue ?? 0)} />
        </div>
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
          <Info label="Belum ada pemilik" value={String(item.ticket_summary?.unassigned ?? 0)} />
          <Info label="Selesai dalam SLA" value={String(item.ticket_summary?.met_sla ?? 0)} />
          <Info label="Melewati SLA" value={String(item.ticket_summary?.breached_sla ?? 0)} />
        </div>
        <p className="mt-4 text-sm text-muted-foreground">Strategi: <span className="font-medium text-foreground">{item.handling_strategy === "direct" ? "Penanganan langsung tanpa tiket wajib" : item.handling_strategy === "multi_ticket" ? "Beberapa workstream tiket" : "Satu workstream tiket"}</span>. Tiket membantu eksekusi; status kasus tetap dikelola di workspace kasus.</p>
        {childTickets.length ? <div className="mt-4 space-y-3">{childTickets.map((ticket) => (
          <article key={ticket.id} className="rounded-lg border border-border bg-surface p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div className="min-w-0">
                <p className="font-medium">{ticket.workstream ? `${ticket.workstream} — ` : ""}{ticket.title}</p>
                <p className="mt-1 break-words text-xs text-muted-foreground">
                  {ticket.id} · {ticket.assignee ?? "Belum ada pemilik"} · {ticket.assignment_group ?? ticket.assigned_unit}
                </p>
                <p className="mt-1 break-words text-xs text-muted-foreground">
                  Keparahan {ticket.severity ?? "-"} · SLA {ticket.sla}{ticket.sla_policy ? ` (${ticket.sla_policy})` : ""}
                  {ticket.due_at ? ` · Target ${fmt(ticket.due_at)}` : ""}
                  {typeof ticket.hours_remaining === "number"
                    ? ` · ${ticket.hours_remaining >= 0 ? `${ticket.hours_remaining} jam tersisa` : `terlambat ${Math.abs(ticket.hours_remaining)} jam`}`
                    : ""}
                </p>
              </div>
              <div className="flex shrink-0 flex-wrap gap-2">
                <StatusBadge label={ticket.status} />
                {ticket.sla_state ? <StatusBadge label={SLA_STATE_LABEL[ticket.sla_state] ?? ticket.sla_state} /> : null}
              </div>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">{ticket.recommended_action}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {TICKET_ACTIONS.filter((status) => (TICKET_TRANSITIONS[ticket.status] ?? TICKET_ACTIONS).includes(status)).map((status) => (
                <button key={status} onClick={() => void updateTicketStatus(ticket, status)} className="rounded-md border border-border px-2.5 py-1.5 text-xs hover:bg-surface-raised">{status}</button>
              ))}
            </div>
          </article>
        ))}</div> : <HelperPanel>Belum ada tiket. Kasus ini tetap aktif dan dapat ditangani langsung.</HelperPanel>}

        <div className="mt-5 space-y-3 rounded-lg border border-dashed border-border p-4">
          <p className="text-sm font-medium">Tambah tiket anak</p>
          <p className="text-xs text-muted-foreground">
            Kolom yang dikosongkan mengikuti aturan default eksplisit: keparahan diwarisi dari kasus
            ({item.severity ?? item.priority_label}), SLA diturunkan dari keparahan tersebut, dan kepemilikan
            mengikuti tim penanganan kasus. Aturan yang dipakai dicatat di jejak audit.
          </p>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <input value={newTicket.title} onChange={(e) => setNewTicket({ ...newTicket, title: e.target.value })} placeholder="Judul tiket (wajib)" className="rounded-md border border-border bg-surface px-3 py-2 text-sm sm:col-span-2" />
            <textarea value={newTicket.description} onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })} placeholder="Deskripsi / konteks kerja" rows={2} className="rounded-md border border-border bg-surface px-3 py-2 text-sm sm:col-span-2" />
            <label className="text-xs text-muted-foreground">Keparahan
              <select value={newTicket.severity} onChange={(e) => setNewTicket({ ...newTicket, severity: e.target.value })} className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground">
                <option value="">Warisi dari kasus ({item.severity ?? item.priority_label})</option>
                {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>
            <label className="text-xs text-muted-foreground">Kebijakan SLA
              <select value={newTicket.sla_policy} onChange={(e) => setNewTicket({ ...newTicket, sla_policy: e.target.value })} className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground">
                <option value="">Turunkan dari keparahan</option>
                {SLA_POLICIES.map((p) => <option key={p.code} value={p.code}>{p.label}</option>)}
              </select>
            </label>
            <label className="text-xs text-muted-foreground">Dampak
              <select value={newTicket.impact} onChange={(e) => setNewTicket({ ...newTicket, impact: e.target.value })} className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground">
                <option value="">Default (Sedang)</option>
                {IMPACTS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>
            <label className="text-xs text-muted-foreground">Urgensi
              <select value={newTicket.urgency} onChange={(e) => setNewTicket({ ...newTicket, urgency: e.target.value })} className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground">
                <option value="">Default (Normal)</option>
                {URGENCIES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>
            <input value={newTicket.assignee} onChange={(e) => setNewTicket({ ...newTicket, assignee: e.target.value })} placeholder={`Penanggung jawab (default: ${item.primary_owner || item.assigned_investigator || "belum ditetapkan di kasus"})`} className="rounded-md border border-border bg-surface px-3 py-2 text-sm" />
            <input value={newTicket.assignment_group} onChange={(e) => setNewTicket({ ...newTicket, assignment_group: e.target.value })} placeholder={`Grup penanganan (default: ${item.handling_team || item.assigned_unit || "belum ditetapkan di kasus"})`} className="rounded-md border border-border bg-surface px-3 py-2 text-sm" />
            <label className="text-xs text-muted-foreground">Target penyelesaian (opsional)
              <input type="datetime-local" value={newTicket.due_at} onChange={(e) => setNewTicket({ ...newTicket, due_at: e.target.value })} className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground" />
            </label>
            <input value={newTicket.category} onChange={(e) => setNewTicket({ ...newTicket, category: e.target.value })} placeholder={`Kategori (default: ${item.issue_category})`} className="rounded-md border border-border bg-surface px-3 py-2 text-sm" />
            <input value={newTicket.workstream} onChange={(e) => setNewTicket({ ...newTicket, workstream: e.target.value })} placeholder="Label workstream (opsional)" className="rounded-md border border-border bg-surface px-3 py-2 text-sm" />
            <textarea value={newTicket.notes} onChange={(e) => setNewTicket({ ...newTicket, notes: e.target.value })} placeholder="Catatan awal (opsional)" rows={2} className="rounded-md border border-border bg-surface px-3 py-2 text-sm sm:col-span-2" />
          </div>
          <button onClick={() => void createChildTicket()} disabled={!newTicket.title.trim()} className="inline-flex items-center justify-center gap-1 rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"><Plus className="h-4 w-4" /> Tambah tiket</button>
        </div>
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

      {/* 7. Kronologi Aktivitas — konteks pendukung, bukan permukaan keputusan:
          diletakkan di bawah bagian aksi dan terlipat secara default. */}
      <SectionCard
        icon={History}
        title="7. Kronologi Aktivitas"
        collapsible
        summary={`${sortedAudit.length} peristiwa${lastEvent ? ` · terakhir ${fmt(lastEvent.timestamp)}` : ""}`}
      >
        <p className="mb-4 break-words text-sm text-muted-foreground">
          Alur kasus: sinyal masuk → kasus dibentuk dan dimonitor → penilaian/penugasan → penanganan langsung atau workstream tiket → resolusi → verifikasi → penutupan.
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

      {/* 8. Jejak Audit */}
      <SectionCard
        icon={History}
        title="8. Jejak Audit"
        collapsible
        summary={`${sortedAudit.length} entri`}
      >
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
  collapsible = false,
  defaultOpen = false,
  summary,
}: {
  icon: typeof FileText;
  title: string;
  children: React.ReactNode;
  /** Render as a native <details> so the section can be folded away. */
  collapsible?: boolean;
  defaultOpen?: boolean;
  /** One-line preview shown while collapsed, so folding costs no context. */
  summary?: string;
}) {
  const heading = (
    <>
      <Icon className="h-5 w-5 shrink-0 text-brand-300" />
      <span className="break-words">{title}</span>
    </>
  );
  const shell = "min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5";

  if (!collapsible) {
    return (
      <section className={shell}>
        <h2 className="flex items-center gap-2 text-lg font-semibold">{heading}</h2>
        <div className="mt-4">{children}</div>
      </section>
    );
  }

  // <details> carries the expanded/collapsed state and keyboard handling
  // natively; no useState, and the content stays findable via browser find.
  return (
    <details open={defaultOpen} className={`group ${shell}`}>
      <summary className="flex cursor-pointer list-none items-center gap-2 text-lg font-semibold [&::-webkit-details-marker]:hidden">
        {heading}
        {summary ? (
          <span className="ml-1 truncate text-sm font-normal text-muted-foreground group-open:hidden">
            {summary}
          </span>
        ) : null}
        <ChevronDown className="ml-auto h-5 w-5 shrink-0 text-muted-foreground transition-transform group-open:rotate-180" />
      </summary>
      <div className="mt-4">{children}</div>
    </details>
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

function OwnerRow({ label, value }: { label: string; value?: string | null }) {
  const empty = !value?.trim();
  return (
    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
      <dt className="text-xs uppercase text-muted-foreground">{label}</dt>
      <dd className={empty ? "text-sm italic text-muted-foreground/70" : "break-words text-sm font-medium"}>
        {empty ? "Belum ditetapkan" : value}
      </dd>
    </div>
  );
}

function OwnerField({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (v: string) => void; placeholder: string }) {
  return (
    <label className="block text-xs">
      <span className="mb-1 block uppercase text-muted-foreground">{label}</span>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="w-full rounded-md border border-border bg-surface-raised px-3 py-2 text-sm text-foreground" />
    </label>
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
