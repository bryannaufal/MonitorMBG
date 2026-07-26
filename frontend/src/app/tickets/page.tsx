"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { api, getWithFallback } from "@/lib/api";
import { fallbackTickets } from "@/lib/demoFallback";
import { caseNumber, ticketEffectivePriority } from "@/lib/utils";
import type { Ticket } from "@/types/monitoring";

// Kolom board (Kanban) — hanya di halaman Tiket Tindak Lanjut.
const COLUMNS = ["Baru", "Sedang Ditinjau", "Menunggu Klarifikasi Vendor", "Verifikasi Lapangan", "Selesai"];
type TicketMessage = { tone: "success" | "warning"; text: string };
type TicketSortBy = "priority" | "recent";
const TICKET_SORT_OPTIONS: { id: TicketSortBy; label: string }[] = [
  { id: "priority", label: "Prioritas tertinggi" },
  { id: "recent", label: "Terbaru diperbarui" },
];

export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<TicketMessage | null>(null);
  const [sortBy, setSortBy] = useState<TicketSortBy>("priority");

  useEffect(() => {
    async function load() {
      const result = await getWithFallback<{ items: Ticket[]; total: number }>("/tickets", {
        items: fallbackTickets,
        total: fallbackTickets.length,
      });
      setTickets(result.data.items);
      setSource(result.source);
      setError(result.error);
      setLoading(false);
    }
    load();
  }, []);

  const byColumn = useMemo(() => {
    const map = new Map<string, Ticket[]>(COLUMNS.map((c) => [c, []]));
    for (const t of tickets) {
      // Normalisasi status yang belum tercakup ke kolom "Sedang Ditinjau".
      const col = COLUMNS.includes(t.status) ? t.status : "Sedang Ditinjau";
      map.get(col)!.push(t);
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
  }, [tickets, sortBy]);

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
      <GovernanceNote compact />
      <HelperPanel>
        Tiket bukan tugas terpisah. Setiap tiket adalah catatan tindakan untuk satu kasus dan mempertahankan tautan bukti,
        perubahan status, unit penanggung jawab, dan riwayat audit.
      </HelperPanel>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile label="Total Tiket" value={String(tickets.length)} />
        <MetricTile label="Terbuka" value={String(tickets.filter((t) => t.status !== "Selesai").length)} />
        <MetricTile label="Verifikasi Lapangan" value={String(tickets.filter((t) => t.status === "Verifikasi Lapangan").length)} />
        <MetricTile label="Selesai" value={String(tickets.filter((t) => t.status === "Selesai").length)} />
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
          {COLUMNS.map((col) => {
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
      <p className="mt-1 break-words text-xs text-muted-foreground">{ticket.linked_region} · {ticket.assigned_unit}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <StatusBadge label={`SLA ${ticket.sla}`} />
        <StatusBadge label={priorityLabel} />
      </div>
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
            {columns.map((c) => (
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
