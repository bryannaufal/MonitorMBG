"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { EntityChip, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { api, getWithFallback } from "@/lib/api";
import { fallbackTickets } from "@/lib/demoFallback";
import { caseNumber, ticketEffectivePriority } from "@/lib/utils";
import type { Ticket, TicketSummary } from "@/types/monitoring";

// Kolom board (Kanban). Mengikuti lifecycle di app/ticketing.py.
const COLUMNS = [
  "Baru",
  "Sedang Ditinjau",
  "Verifikasi Lapangan",
  "Menunggu Klarifikasi Vendor",
  "Ditahan / On Hold",
  "Selesai",
  "Ditutup",
];

// Transisi yang diizinkan backend; menu "Pindahkan ke" hanya menawarkan ini
// supaya operator tidak menabrak 422.
const TRANSITIONS: Record<string, string[]> = {
  "Baru": ["Sedang Ditinjau", "Verifikasi Lapangan", "Menunggu Klarifikasi Vendor", "Ditahan / On Hold", "Dibatalkan"],
  "Sedang Ditinjau": ["Verifikasi Lapangan", "Menunggu Klarifikasi Vendor", "Ditahan / On Hold", "Selesai", "Dibatalkan"],
  "Verifikasi Lapangan": ["Sedang Ditinjau", "Menunggu Klarifikasi Vendor", "Ditahan / On Hold", "Selesai", "Dibatalkan"],
  "Menunggu Klarifikasi Vendor": ["Sedang Ditinjau", "Verifikasi Lapangan", "Ditahan / On Hold", "Selesai", "Dibatalkan"],
  "Ditahan / On Hold": ["Sedang Ditinjau", "Verifikasi Lapangan", "Menunggu Klarifikasi Vendor", "Dibatalkan"],
  "Selesai": ["Ditutup", "Sedang Ditinjau"],
  "Ditutup": ["Sedang Ditinjau"],
  "Dibatalkan": [],
};

const SLA_STATE_LABEL: Record<string, string> = {
  on_track: "On track", at_risk: "Berisiko", overdue: "Terlambat",
  paused: "SLA dijeda", met: "Selesai dalam SLA", breached: "Melewati SLA",
  unknown: "SLA tidak diketahui",
};

type TicketMessage = { tone: "success" | "warning"; text: string };
type TicketsResponse = { items: Ticket[]; total: number; summary?: TicketSummary };

type TicketSortBy = "priority" | "recent";
const TICKET_SORT_OPTIONS: { id: TicketSortBy; label: string }[] = [
  { id: "priority", label: "Prioritas tertinggi" },
  { id: "recent", label: "Terbaru diperbarui" },
];

export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [summary, setSummary] = useState<TicketSummary | null>(null);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<TicketMessage | null>(null);
  const [slaFilter, setSlaFilter] = useState("");
  const [onlyUnassigned, setOnlyUnassigned] = useState(false);
  const [sortBy, setSortBy] = useState<TicketSortBy>("priority");

  useEffect(() => {
    async function load() {
      const result = await getWithFallback<TicketsResponse>("/tickets", {
        items: fallbackTickets,
        total: fallbackTickets.length,
      });
      setTickets(result.data.items);
      setSummary(result.data.summary ?? null);
      setSource(result.source);
      setError(result.error);
      setLoading(false);
    }
    load();
  }, []);

  const visible = useMemo(() => tickets.filter((t) => {
    if (slaFilter && t.sla_state !== slaFilter) return false;
    if (onlyUnassigned && (t.assignee ?? "").trim()) return false;
    return true;
  }), [tickets, slaFilter, onlyUnassigned]);

  const byColumn = useMemo(() => {
    const map = new Map<string, Ticket[]>(COLUMNS.map((c) => [c, []]));
    for (const t of visible) {
      // Status di luar board (mis. "Dibatalkan") mendapat kolomnya sendiri
      // daripada disamarkan sebagai "Sedang Ditinjau" — status yang keliru
      // tampil lebih berbahaya daripada kolom tambahan.
      if (!map.has(t.status)) map.set(t.status, []);
      map.get(t.status)!.push(t);
    }
    for (const col of COLUMNS) {
      map.get(col)!.sort((a, b) => {
        if (sortBy === "priority") {
          const diff = ticketEffectivePriority(b) - ticketEffectivePriority(a);
          if (diff !== 0) return diff;
        }
        return Date.parse(b.updated_at) - Date.parse(a.updated_at);
      });
    }
    return map;
  }, [visible, sortBy]);

  async function moveTicket(ticket: Ticket, status: string) {
    const updated = { ...ticket, status, updated_at: new Date().toISOString() };
    if (source === "fallback") {
      setTickets((cur) => cur.map((t) => (t.id === ticket.id ? updated : t)));
      setMessage({ tone: "warning", text: `${ticket.id} dipindahkan ke "${status}" pada data demo lokal. Jejak audit backend tidak ditulis.` });
      return;
    }
    setMessage(null);
    try {
      const result = await api.patch<{ ticket: Ticket }, { status: string; note: string }>(
        `/tickets/${ticket.id}/status`,
        { status, note: `Aksi antrean tiket: ${status}` },
      );
      setTickets((cur) => cur.map((t) => (t.id === ticket.id ? result.ticket : t)));
      setMessage({ tone: "success", text: `${ticket.id} dipindahkan ke "${status}". Jejak audit diperbarui di API demo.` });
    } catch {
      setMessage({ tone: "warning", text: `${ticket.id} gagal diperbarui. Pembaruan backend gagal, jejak audit tidak tercatat. Coba lagi.` });
    }
  }

  // Backend is the source of truth for counters; the local tally is only for
  // the offline demo fallback, and uses the same bucket definitions.
  const counters: TicketSummary = summary ?? {
    total: tickets.length,
    open: tickets.filter((t) => t.status === "Baru").length,
    in_progress: tickets.filter((t) => ["Sedang Ditinjau", "Verifikasi Lapangan"].includes(t.status)).length,
    waiting: tickets.filter((t) => ["Menunggu Klarifikasi Vendor", "Ditahan / On Hold"].includes(t.status)).length,
    resolved: tickets.filter((t) => t.status === "Selesai").length,
    closed: tickets.filter((t) => ["Ditutup", "Dibatalkan"].includes(t.status)).length,
    completed: tickets.filter((t) => ["Selesai", "Ditutup", "Dibatalkan"].includes(t.status)).length,
    on_track: tickets.filter((t) => t.sla_state === "on_track").length,
    at_risk: tickets.filter((t) => t.at_risk).length,
    overdue: tickets.filter((t) => t.overdue).length,
    paused: tickets.filter((t) => t.sla_state === "paused").length,
    met_sla: tickets.filter((t) => t.sla_state === "met").length,
    breached_sla: tickets.filter((t) => t.sla_state === "breached").length,
    unassigned: tickets.filter((t) => !(t.assignee ?? "").trim()).length,
  };

  async function confirmSuggested(ticket: Ticket) {
    try {
      const result = await api.patch<{ ticket: Ticket }, Record<string, never>>(`/tickets/${ticket.id}/priority/confirm`, {});
      setTickets((cur) => cur.map((t) => (t.id === ticket.id ? result.ticket : t)));
      setMessage({ tone: "success", text: `Prioritas suggested dikonfirmasi untuk ${ticket.id}.` });
    } catch {
      setMessage({ tone: "warning", text: "Gagal konfirmasi prioritas." });
    }
  }

  if (loading) return <LoadingState />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tiket Tindak Lanjut"
        description="Papan tindakan operasional untuk kasus pengawasan terhubung: penanganan SLA, penugasan, eskalasi, dan penyelesaian."
        breadcrumbs={[{ label: "Pusat Kendali", href: "/" }, { label: "Tiket Tindak Lanjut" }]}
        source={source}
        error={error}
      />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        <MetricTile label="Total Tiket" value={String(counters.total)} />
        <MetricTile label="Baru" value={String(counters.open)} />
        <MetricTile label="Dikerjakan" value={String(counters.in_progress)} />
        <MetricTile label="Menunggu" value={String(counters.waiting)} />
        <MetricTile label="Selesai" value={String(counters.completed)} />
        <MetricTile label="On track" value={String(counters.on_track)} />
        <MetricTile label="Berisiko" value={String(counters.at_risk)} />
        <MetricTile label="Terlambat" value={String(counters.overdue)} />
        <MetricTile label="Belum ada pemilik" value={String(counters.unassigned)} />
        <MetricTile label="Melewati SLA" value={String(counters.breached_sla)} />
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-surface-raised p-3">
        <label className="text-xs text-muted-foreground">
          <span className="mr-2">Status SLA</span>
          <select value={slaFilter} onChange={(e) => setSlaFilter(e.target.value)} className="rounded-md border border-border bg-surface px-2 py-1.5 text-xs text-foreground">
            <option value="">Semua</option>
            {Object.entries(SLA_STATE_LABEL).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 text-xs text-muted-foreground">
          <input type="checkbox" checked={onlyUnassigned} onChange={(e) => setOnlyUnassigned(e.target.checked)} className="rounded border-border" />
          Hanya yang belum punya pemilik
        </label>
        <span className="text-xs text-muted-foreground">Menampilkan {visible.length} dari {tickets.length} tiket.</span>
      </div>

      {message ? <p className={messageClass(message.tone)}>{message.text}</p> : null}

      <section className="rounded-xl border border-border bg-surface-raised p-4">
        <label className="block min-w-[12rem] max-w-xs text-xs">
          <span className="mb-1 block uppercase text-muted-foreground">Urutkan tiket</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as TicketSortBy)}
            className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground"
          >
            {TICKET_SORT_OPTIONS.map((opt) => (
              <option key={opt.id} value={opt.id}>{opt.label}</option>
            ))}
          </select>
        </label>
      </section>

      <div className="overflow-x-auto pb-2">
        <div className="flex min-w-max gap-4">
          {[...byColumn.keys()].map((col) => {
            const items = byColumn.get(col) ?? [];
            return (
              <div key={col} className="flex w-80 shrink-0 flex-col rounded-xl border border-border bg-surface-raised">
                <div className="flex items-center justify-between border-b border-border px-4 py-3">
                  <h2 className="break-words text-sm font-semibold">{col}</h2>
                  <span className="rounded-full bg-surface-overlay px-2 py-0.5 text-xs text-muted-foreground">{items.length}</span>
                </div>
                <div className="flex flex-col gap-3 p-3">
                  {items.length === 0 ? (
                    <p className="px-1 py-6 text-center text-xs text-muted-foreground">Tidak ada tiket.</p>
                  ) : (
                    items.map((ticket) => (
                      <TicketCard key={ticket.id} ticket={ticket} columns={COLUMNS} current={col} onMove={moveTicket} onConfirm={confirmSuggested} />
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function TicketCard({
  ticket,
  columns,
  current,
  onMove,
  onConfirm,
}: {
  ticket: Ticket;
  columns: string[];
  current: string;
  onMove: (ticket: Ticket, status: string) => void;
  onConfirm: (ticket: Ticket) => void;
}) {
  const priorityLabel =
    ticket.priority_mode === "suggested"
      ? `Suggested: ${ticket.suggested_priority_label ?? ticket.escalation_level} (${ticket.suggested_priority ?? ticket.priority})`
      : ticket.priority_mode === "manual"
        ? `Manual: ${ticket.priority_label ?? ticket.escalation_level}`
        : ticket.escalation_level;

  return (
    <article className="min-w-0 rounded-lg border border-border bg-surface p-4">
      <div className="flex flex-wrap gap-2">
        <EntityChip label={ticket.id} tone="ticket" />
        <EntityChip label={caseNumber(ticket.case_id)} href={`/cases/${ticket.case_id}`} tone="case" />
        {ticket.origin === "auto" ? <StatusBadge label="Auto" /> : null}
      </div>
      <h3 className="mt-2 break-words text-sm font-semibold">{ticket.title}</h3>
      <p className="mt-1 break-words text-xs text-muted-foreground">{ticket.linked_region} · {ticket.assignment_group ?? ticket.assigned_unit}</p>
      <p className="mt-1 break-words text-xs text-muted-foreground">
        Pemilik: {ticket.assignee ?? <span className="text-amber-600 dark:text-amber-400">belum ditetapkan</span>}
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <StatusBadge label={`SLA ${ticket.sla}${ticket.sla_policy ? ` · ${ticket.sla_policy}` : ""}`} />
        <StatusBadge label={priorityLabel} />
        {ticket.sla_state ? <StatusBadge label={SLA_STATE_LABEL[ticket.sla_state] ?? ticket.sla_state} /> : null}
      </div>
      {typeof ticket.hours_remaining === "number" ? (
        <p className="mt-2 break-words text-xs text-muted-foreground">
          {ticket.hours_remaining >= 0
            ? `${ticket.hours_remaining} jam tersisa`
            : `Terlambat ${Math.abs(ticket.hours_remaining)} jam`}
          {ticket.due_at ? ` · target ${new Date(ticket.due_at).toLocaleString("id-ID")}` : ""}
        </p>
      ) : null}
      <p className="mt-3 break-words text-xs text-muted-foreground">{ticket.recommended_action}</p>
      {ticket.priority_mode === "suggested" ? (
        <button
          type="button"
          onClick={() => onConfirm(ticket)}
          className="mt-3 w-full rounded-md border border-brand-500/40 bg-brand-500/10 px-3 py-2 text-xs font-medium text-brand-800 dark:text-brand-200"
        >
          Konfirmasi Prioritas Suggested
        </button>
      ) : null}
      <div className="mt-3 flex flex-col gap-2">
        <Link href={`/cases/${ticket.case_id}`} className="inline-flex justify-center rounded-md bg-brand-500 px-3 py-2 text-xs font-medium text-white hover:bg-brand-400">
          Buka Kasus
        </Link>
        <label className="text-xs text-muted-foreground">
          <span className="mb-1 block">Pindahkan ke</span>
          <select
            value={current}
            onChange={(e) => onMove(ticket, e.target.value)}
            className="w-full rounded-md border border-border bg-surface-raised px-2 py-1.5 text-xs text-foreground"
          >
            <option value={current}>{current} (saat ini)</option>
            {(TRANSITIONS[current] ?? columns).map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>
      </div>
    </article>
  );
}

function messageClass(tone: TicketMessage["tone"]) {
  return tone === "success"
    ? "rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-800 dark:text-emerald-200"
    : "rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-800 dark:text-amber-200";
}
