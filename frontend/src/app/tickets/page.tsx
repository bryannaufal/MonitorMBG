"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { api, getWithFallback } from "@/lib/api";
import { fallbackTickets } from "@/lib/demoFallback";
import type { Ticket } from "@/types/monitoring";

const statuses = ["Under Review", "Waiting Vendor Clarification", "Escalated", "Field Verification Scheduled", "Resolved"];

export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);

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

  async function updateStatus(ticket: Ticket, status: string) {
    const updated = { ...ticket, status, updated_at: new Date().toISOString() };
    setTickets((current) => current.map((item) => (item.id === ticket.id ? updated : item)));
    setMessage(`${ticket.id} moved to ${status}. The linked case audit trail records this action in live API mode.`);
    try {
      const result = await api.patch<{ ticket: Ticket }, { status: string; note: string }>(
        `/tickets/${ticket.id}/status`,
        { status, note: `Ticket queue action: ${status}` },
      );
      setTickets((current) => current.map((item) => (item.id === ticket.id ? result.ticket : item)));
    } catch {
      setSource("fallback");
    }
  }

  if (loading) return <LoadingState />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Ticket Queue"
        description="Operational action layer for linked oversight cases, SLA handling, assignment, escalation, and resolution."
        breadcrumbs={[{ label: "Command Center", href: "/" }, { label: "Tickets" }]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Tickets are not separate tasks. Each ticket is the action record for a case and should preserve evidence links, status changes, assigned unit, and audit history.
      </HelperPanel>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile label="Tickets" value={String(tickets.length)} />
        <MetricTile label="Open" value={String(tickets.filter((item) => item.status !== "Resolved").length)} />
        <MetricTile label="Escalated" value={String(tickets.filter((item) => item.status.includes("Escalated")).length)} />
        <MetricTile label="Resolved" value={String(tickets.filter((item) => item.status === "Resolved").length)} />
      </div>

      {message ? <p className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-200">{message}</p> : null}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {tickets.map((ticket) => (
          <article key={ticket.id} className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap gap-2">
                  <EntityChip label={ticket.id} tone="ticket" />
                  <EntityChip label={ticket.case_id} href={`/cases/${ticket.case_id}`} tone="case" />
                  <EntityChip label={ticket.linked_vendor_name} href={`/vendors/${ticket.linked_vendor_id}`} tone="vendor" />
                </div>
                <h2 className="mt-3 break-words text-lg font-semibold">{ticket.title}</h2>
                <p className="break-words text-sm text-muted-foreground">{ticket.linked_region} · {ticket.assigned_unit}</p>
              </div>
              <StatusBadge label={ticket.status} />
            </div>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Info label="SLA" value={ticket.sla} />
              <Info label="Priority" value={String(ticket.priority)} />
              <Info label="Escalation" value={ticket.escalation_level} />
              <Info label="Last Update" value={new Date(ticket.updated_at).toLocaleString()} />
            </div>
            <p className="mt-4 break-words text-sm text-muted-foreground">{ticket.recommended_action}</p>
            <div className="mt-4 break-words rounded-lg bg-surface p-3 text-sm text-muted-foreground">
              Evidence #{ticket.linked_evidence_ids.join(", #")} · {ticket.audit_preview}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link href={`/cases/${ticket.case_id}`} className="inline-flex justify-center rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">
                Open Case
              </Link>
              {statuses.map((status) => (
                <button
                  key={status}
                  onClick={() => updateStatus(ticket, status)}
                  className="rounded-md border border-border px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-surface hover:text-foreground"
                >
                  {status}
                </button>
              ))}
            </div>
          </article>
        ))}
      </div>
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
