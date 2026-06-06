"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Bot } from "lucide-react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { api, getWithFallback } from "@/lib/api";
import { fallbackCases } from "@/lib/demoFallback";
import type { AuditTrailEvent, OversightCase, Ticket } from "@/types/monitoring";

const tabs = ["overview", "signals", "evidence", "scoring", "ticket", "copilot", "audit trail"];
const ticketActions = [
  "Under Review",
  "Waiting Vendor Clarification",
  "Escalated",
  "Field Verification Scheduled",
  "Resolved",
];

export default function CaseDetailPage() {
  const params = useParams<{ id: string }>();
  const fallback = fallbackCases.find((item) => item.case_id === params.id) ?? fallbackCases[0];
  const [item, setItem] = useState<OversightCase | null>(null);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [actionNote, setActionNote] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const result = await getWithFallback<OversightCase>(`/cases/${params.id}`, fallback);
      setItem(result.data);
      setSource(result.source);
      setError(result.error);
      setLoading(false);
    }
    load();
  }, [fallback, params.id]);

  useEffect(() => {
    const requestedTab = new URLSearchParams(window.location.search).get("tab")?.replace("-", " ");
    if (requestedTab && tabs.includes(requestedTab)) setActiveTab(requestedTab);
  }, []);

  const sortedAudit = useMemo(() => {
    return [...(item?.audit_events ?? [])].sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp));
  }, [item?.audit_events]);

  async function updateTicketStatus(status: string) {
    if (!item?.ticket) return;
    const optimisticTicket: Ticket = { ...item.ticket, status, updated_at: new Date().toISOString() };
    const auditEvent: AuditTrailEvent = {
      id: Date.now(),
      case_id: item.case_id,
      ticket_id: optimisticTicket.id,
      event_type: "status_changed",
      actor: "Demo Operator",
      role: "District Operator",
      description: `Ticket status changed to ${status}.`,
      timestamp: optimisticTicket.updated_at,
    };
    setItem({ ...item, status, ticket: optimisticTicket, audit_events: [auditEvent, ...item.audit_events] });
    setActionNote(`Ticket ${optimisticTicket.id} updated to ${status}. Audit trail event recorded.`);

    try {
      const result = await api.patch<{ ticket: Ticket; audit_event: AuditTrailEvent }, { status: string; note: string }>(
        `/tickets/${item.ticket.id}/status`,
        { status, note: `Case ${item.case_id} demo action: ${status}` },
      );
      setItem((current) =>
        current
          ? {
              ...current,
              status,
              ticket: result.ticket,
              audit_events: [result.audit_event, ...current.audit_events.filter((event) => event.id !== auditEvent.id)],
            }
          : current,
      );
    } catch {
      setSource("fallback");
    }
  }

  if (loading || !item) return <LoadingState />;

  return (
    <div className="space-y-6">
      <PageHeader
        title={item.title}
        description="Case Detail / Investigation Hub connecting signals, evidence, scoring, tickets, copilot synthesis, audit trail, and vendor risk learning."
        breadcrumbs={[
          { label: "Command Center", href: "/" },
          { label: "Cases", href: "/cases" },
          { label: item.case_id },
        ]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />

      <section className="rounded-xl border border-border bg-surface-raised p-5">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <div className="flex flex-wrap gap-2">
              <StatusBadge label={item.priority_label} />
              <StatusBadge label={item.status} />
              <EntityChip label={item.vendor_name} href={`/vendors/${item.vendor_id}`} tone="vendor" />
              {item.ticket_id ? <EntityChip label={item.ticket_id} tone="ticket" /> : null}
            </div>
            <p className="mt-4 max-w-4xl text-sm leading-6 text-muted-foreground">{item.summary}</p>
          </div>
          <div className="grid min-w-[280px] grid-cols-2 gap-3 text-sm">
            <Info label="Region/School" value={`${item.school}, ${item.region}`} />
            <Info label="SLA" value={item.sla_status} />
            <Info label="Assigned Unit" value={item.assigned_unit} />
            <Info label="Action" value={item.recommended_action} />
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
        <MetricTile label="Severity" value={String(item.score.severity_score)} />
        <MetricTile label="Confidence" value={String(item.score.confidence_score)} />
        <MetricTile label="Nutrition" value={String(item.score.nutrition_concern_score)} />
        <MetricTile label="Cost Anomaly" value={String(item.score.cost_anomaly_score)} />
        <MetricTile label="Final Priority" value={String(item.score.final_priority_score)} detail={item.score.priority_label} />
      </div>

      <div className="flex flex-wrap gap-2 rounded-xl border border-border bg-surface-raised p-2">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`rounded-md px-3 py-2 text-sm font-medium capitalize transition-colors ${
              activeTab === tab ? "bg-brand-500 text-white" : "text-muted-foreground hover:bg-surface hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "overview" ? <OverviewTab item={item} /> : null}
      {activeTab === "signals" ? <SignalsTab item={item} /> : null}
      {activeTab === "evidence" ? <EvidenceTab item={item} /> : null}
      {activeTab === "scoring" ? <ScoringTab item={item} /> : null}
      {activeTab === "ticket" ? <TicketTab item={item} actionNote={actionNote} onAction={updateTicketStatus} /> : null}
      {activeTab === "copilot" ? <CopilotTab item={item} /> : null}
      {activeTab === "audit trail" ? <AuditTab events={sortedAudit} /> : null}
    </div>
  );
}

function OverviewTab({ item }: { item: OversightCase }) {
  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <section className="rounded-xl border border-border bg-surface-raised p-5 xl:col-span-2">
        <h2 className="text-lg font-semibold">Overview</h2>
        <div className="mt-4 space-y-4 text-sm leading-6 text-muted-foreground">
          <p><span className="font-medium text-foreground">What happened: </span>{item.what_happened}</p>
          <p><span className="font-medium text-foreground">Why it matters: </span>{item.why_it_matters}</p>
          <p><span className="font-medium text-foreground">Risk explanation: </span>{item.risk_explanation}</p>
          <p><span className="font-medium text-foreground">Recommended action: </span>{item.recommended_action}</p>
        </div>
      </section>
      <section className="rounded-xl border border-border bg-surface-raised p-5">
        <h2 className="text-lg font-semibold">Related Entities</h2>
        <div className="mt-4 flex flex-wrap gap-2">
          <EntityChip label={item.case_id} tone="case" />
          <EntityChip label={item.vendor_name} href={`/vendors/${item.vendor_id}`} tone="vendor" />
          {item.ticket_id ? <EntityChip label={item.ticket_id} tone="ticket" /> : null}
          <EntityChip label={`${item.evidence_count} evidence`} tone="evidence" />
          <EntityChip label={`Score ${item.score.final_priority_score}`} tone="score" />
          <EntityChip label={`${item.audit_events.length} audit events`} tone="audit" />
        </div>
        <Link href={`/vendors/${item.vendor_id}`} className="mt-5 inline-flex rounded-md border border-border px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-surface">
          Open Vendor Profile
        </Link>
      </section>
    </div>
  );
}

function SignalsTab({ item }: { item: OversightCase }) {
  const signals = [
    ...item.complaints.map((signal) => ({
      id: `complaint-${signal.id}`,
      source: signal.source,
      summary: signal.summary,
      category: signal.issue_category,
      severity: signal.severity_score,
      confidence: Math.round(signal.source_confidence * 100),
      timestamp: signal.created_at,
      status: signal.status,
      evidence: "Public signal evidence",
    })),
    ...item.reports.map((signal) => ({
      id: `report-${signal.id}`,
      source: signal.reporter_type,
      summary: signal.summary,
      category: "official report",
      severity: signal.linked_risk_score,
      confidence: signal.completeness_score,
      timestamp: signal.submitted_at,
      status: signal.status,
      evidence: `${signal.evidence_count} evidence items`,
    })),
    ...item.daily_reports.map((signal) => ({
      id: `daily-${signal.id}`,
      source: "Daily Vendor Report",
      summary: `${signal.planned_menu} planned; ${signal.actual_menu} delivered`,
      category: signal.mismatch_indicator ? "menu mismatch" : "daily evidence",
      severity: signal.cost_estimate.cost_anomaly_flag ? 82 : 58,
      confidence: signal.document_complete ? 78 : 54,
      timestamp: signal.delivery_timestamp,
      status: signal.verification_status,
      evidence: `${signal.photo_evidence_count} photos`,
    })),
  ];

  return (
    <section className="rounded-xl border border-border bg-surface-raised p-5">
      <h2 className="text-lg font-semibold">Connected Intake Signals</h2>
      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        {signals.map((signal) => (
          <article key={signal.id} className="rounded-lg border border-border bg-surface p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium">{signal.summary}</p>
                <p className="mt-1 text-xs text-muted-foreground">{signal.source} · {new Date(signal.timestamp).toLocaleString()}</p>
              </div>
              <StatusBadge label={signal.status} />
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <StatusBadge label={signal.category} />
              <EntityChip label={`Severity ${signal.severity}`} tone="score" />
              <EntityChip label={`Confidence ${signal.confidence}%`} />
              <EntityChip label={signal.evidence} tone="evidence" />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function EvidenceTab({ item }: { item: OversightCase }) {
  return (
    <section className="rounded-xl border border-border bg-surface-raised p-5">
      <h2 className="text-lg font-semibold">Evidence Review</h2>
      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        {item.evidence.map((evidence) => (
          <article key={evidence.id} className="rounded-lg border border-border bg-surface p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium">{evidence.title}</p>
                <p className="mt-1 text-xs text-muted-foreground">{evidence.linked_entity} · {new Date(evidence.created_at).toLocaleString()}</p>
              </div>
              <StatusBadge label={evidence.type} />
            </div>
            <div className="mt-3 grid grid-cols-3 gap-3">
              <Info label="Confidence" value={`${Math.round(evidence.confidence_score * 100)}%`} />
              <Info label="Image/Text" value={evidence.image_text_match_score == null ? "N/A" : `${Math.round(evidence.image_text_match_score * 100)}%`} />
              <Info label="Duplicate" value={evidence.duplicate_score == null ? "N/A" : `${Math.round(evidence.duplicate_score * 100)}%`} />
            </div>
            {evidence.ocr_result ? <p className="mt-3 rounded-lg bg-surface-overlay p-3 text-sm text-muted-foreground">{evidence.ocr_result}</p> : null}
            <p className="mt-3 text-sm text-muted-foreground">{evidence.reviewer_note}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <StatusBadge label={evidence.ai_signal} />
              <EntityChip label="Confidence impact to score" tone="score" />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ScoringTab({ item }: { item: OversightCase }) {
  const score = item.score;
  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <section className="rounded-xl border border-border bg-surface-raised p-5 xl:col-span-2">
        <h2 className="text-lg font-semibold">Risk Scoring Factors</h2>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          <ScoreBar label="Severity" value={score.severity_score} />
          <ScoreBar label="Confidence" value={score.confidence_score} />
          <ScoreBar label="Nutrition Concern" value={score.nutrition_concern_score} />
          <ScoreBar label="Cost Anomaly" value={score.cost_anomaly_score} />
          <ScoreBar label="Anomaly/Spike" value={score.anomaly_score} />
          <ScoreBar label="Final Priority" value={score.final_priority_score} />
        </div>
      </section>
      <section className="rounded-xl border border-border bg-surface-raised p-5">
        <h2 className="text-lg font-semibold">Explanation</h2>
        <div className="mt-4">
          <StatusBadge label={score.priority_label} />
          <p className="mt-3 text-sm leading-6 text-muted-foreground">{score.explanation}</p>
          <p className="mt-4 text-sm font-medium">Recommended action</p>
          <p className="mt-2 text-sm text-muted-foreground">{score.recommended_action}</p>
        </div>
      </section>
    </div>
  );
}

function TicketTab({
  item,
  actionNote,
  onAction,
}: {
  item: OversightCase;
  actionNote: string | null;
  onAction: (status: string) => void;
}) {
  if (!item.ticket) {
    return <HelperPanel>No ticket is linked yet. Create a ticket from the case queue during the live workflow.</HelperPanel>;
  }

  return (
    <section className="rounded-xl border border-border bg-surface-raised p-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-lg font-semibold">{item.ticket.title}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{item.ticket.id} · {item.assigned_unit}</p>
        </div>
        <StatusBadge label={item.ticket.status} />
      </div>
      <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-4">
        <Info label="SLA" value={item.ticket.sla} />
        <Info label="Escalation" value={item.ticket.escalation_level} />
        <Info label="Evidence" value={`${item.ticket.linked_evidence_ids.length} linked`} />
        <Info label="Last Update" value={new Date(item.ticket.updated_at).toLocaleString()} />
      </div>
      <p className="mt-4 text-sm leading-6 text-muted-foreground">{item.ticket.recommended_action}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        {ticketActions.map((status) => (
          <button
            key={status}
            onClick={() => onAction(status)}
            className="rounded-md border border-border px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-surface hover:text-foreground"
          >
            {status}
          </button>
        ))}
      </div>
      {actionNote ? <p className="mt-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-200">{actionNote}</p> : null}
    </section>
  );
}

function CopilotTab({ item }: { item: OversightCase }) {
  const questions = [
    "Summarize this case.",
    "Why is this high priority?",
    "What evidence supports the score?",
    "What should the operator do next?",
    "Which vendor history is relevant?",
  ];
  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <section className="rounded-xl border border-border bg-surface-raised p-5">
        <h2 className="text-lg font-semibold">Suggested Questions</h2>
        <div className="mt-4 space-y-2">
          {questions.map((question) => (
            <button key={question} className="flex w-full items-center gap-2 rounded-lg border border-border bg-surface p-3 text-left text-sm text-muted-foreground hover:text-foreground">
              <Bot className="h-4 w-4 text-brand-300" />
              {question}
            </button>
          ))}
        </div>
      </section>
      <section className="rounded-xl border border-border bg-surface-raised p-5 xl:col-span-2">
        <h2 className="text-lg font-semibold">Generated Case Summary</h2>
        <p className="mt-4 text-sm leading-6 text-muted-foreground">
          {item.case_id} is {item.priority_label.toLowerCase()} priority because {item.vendor_name} has linked signals for {item.issue_category}, evidence confidence of {item.score.confidence_score}, and final priority score {item.score.final_priority_score}. Recommended next step: {item.recommended_action}
        </p>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
          {item.copilot_sources.map((source) => (
            <div key={`${source.source_type}-${source.source_id}`} className="rounded-lg border border-border bg-surface p-3">
              <StatusBadge label={source.label} />
              <p className="mt-2 text-sm font-medium">{source.title}</p>
              <p className="mt-1 text-xs text-muted-foreground">{source.source_type}:{source.source_id}</p>
            </div>
          ))}
        </div>
        <HelperPanel>
          AI-assisted synthesis based on demo evidence. Final decision requires authorized operator review.
        </HelperPanel>
      </section>
    </div>
  );
}

function AuditTab({ events }: { events: AuditTrailEvent[] }) {
  return (
    <section className="rounded-xl border border-border bg-surface-raised p-5">
      <h2 className="text-lg font-semibold">Case Audit Trail</h2>
      <div className="mt-4 space-y-3">
        {events.map((event) => (
          <div key={event.id} className="grid gap-4 rounded-lg border border-border bg-surface p-4 md:grid-cols-[180px_1fr_180px]">
            <div>
              <p className="font-mono text-xs text-brand-300">{event.case_id}</p>
              <p className="mt-1 text-xs text-muted-foreground">{new Date(event.timestamp).toLocaleString()}</p>
            </div>
            <div>
              <StatusBadge label={event.event_type.replaceAll("_", " ")} />
              <p className="mt-3 text-sm text-muted-foreground">{event.description}</p>
            </div>
            <div className="text-sm">
              <p className="font-medium">{event.actor}</p>
              <p className="text-muted-foreground">{event.role}</p>
              <p className="font-mono text-xs text-muted-foreground">{event.ticket_id}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-surface p-3">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium">{value}</p>
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-sm font-semibold">{value}</p>
      </div>
      <div className="mt-3 h-2 rounded-full bg-surface-overlay">
        <div className="h-2 rounded-full bg-brand-500" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
