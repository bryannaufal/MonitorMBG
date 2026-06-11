"use client";

import { useEffect, useState } from "react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { asList, fallbackAudit } from "@/lib/demoFallback";
import type { AuditTrailEvent, ListResponse } from "@/types/monitoring";

export default function AuditTrailPage() {
  const [events, setEvents] = useState<AuditTrailEvent[]>([]);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const result = await getWithFallback<ListResponse<AuditTrailEvent>>("/audit-trail?size=100", asList(fallbackAudit));
      setEvents(result.data.items);
      setSource(result.source);
      setError(result.error);
      setLoading(false);
    }
    load();
  }, []);

  if (loading) return <LoadingState />;

  const sorted = [...events].sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Governance Log"
        description="Accountability timeline for AI scoring, evidence review, ticket changes, operator actions, escalations, and resolutions."
        breadcrumbs={[{ label: "Command Center", href: "/" }, { label: "Governance Log" }]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        The governance log answers whether a case can be traced from intake through scoring, action, human review, and resolution.
      </HelperPanel>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile label="Events" value={String(events.length)} />
        <MetricTile label="AI-Assisted" value={String(events.filter((event) => event.role.includes("AI") || event.actor.includes("AI")).length)} />
        <MetricTile label="Operator Reviewed" value={String(events.filter((event) => event.role.includes("Operator")).length)} />
        <MetricTile label="Escalations" value={String(events.filter((event) => event.event_type.includes("escalation")).length)} />
      </div>

      <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
        <div className="space-y-4">
          {sorted.map((event) => (
            <div key={event.id} className="grid min-w-0 gap-4 rounded-lg border border-border bg-surface p-4 lg:grid-cols-[170px_minmax(0,1fr)_190px] xl:grid-cols-[190px_minmax(0,1fr)_220px]">
              <div className="min-w-0">
                <EntityChip label={event.case_id} href={`/cases/${event.case_id}?tab=audit-trail`} tone="case" />
                <p className="mt-2 text-xs text-muted-foreground">{new Date(event.timestamp).toLocaleString()}</p>
              </div>
              <div className="min-w-0">
                <div className="flex flex-wrap gap-2">
                  <StatusBadge label={event.event_type.replaceAll("_", " ")} />
                  <StatusBadge label={classifyEvent(event)} />
                </div>
                <p className="mt-3 break-words text-sm text-muted-foreground">{event.description}</p>
              </div>
              <div className="min-w-0 text-sm">
                <p className="break-words font-medium">{event.actor}</p>
                <p className="break-words text-muted-foreground">{event.role}</p>
                <div className="mt-2">
                  <EntityChip label={event.ticket_id} tone="ticket" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function classifyEvent(event: AuditTrailEvent) {
  if (event.event_type.includes("copilot") || event.role.includes("AI")) return "AI-Assisted";
  if (event.event_type.includes("escalation")) return "Escalated";
  if (event.event_type.includes("resolved")) return "Resolved";
  if (event.role.includes("Operator") || event.role.includes("Supervisor")) return "Operator Reviewed";
  return "System Generated";
}
