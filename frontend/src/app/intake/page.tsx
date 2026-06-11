"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ClipboardList, FileText, MessageSquareWarning } from "lucide-react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { asList, fallbackComplaints, fallbackDailyReports, fallbackReports } from "@/lib/demoFallback";
import type { Complaint, DailyReport, ListResponse, Report } from "@/types/monitoring";

type IntakeSignal = {
  id: string;
  tab: "all" | "complaints" | "reports" | "daily-reports";
  sourceType: string;
  summary: string;
  issueCategory: string;
  vendorId: string;
  vendorName: string;
  region: string;
  school: string;
  severity: number;
  confidence: number;
  status: string;
  caseId: string;
  timestamp: string;
};

const tabs = [
  { id: "all", label: "All Signals" },
  { id: "complaints", label: "Public Complaints" },
  { id: "reports", label: "Official Reports" },
  { id: "daily-reports", label: "Daily Reports" },
];

export default function IntakePage() {
  const [activeTab, setActiveTab] = useState("all");
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [dailyReports, setDailyReports] = useState<DailyReport[]>([]);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const [complaintResult, reportResult, dailyResult] = await Promise.all([
        getWithFallback<ListResponse<Complaint>>("/complaints?size=100", asList(fallbackComplaints)),
        getWithFallback<ListResponse<Report>>("/reports?size=100", asList(fallbackReports)),
        getWithFallback<ListResponse<DailyReport>>("/daily-reports?size=100", asList(fallbackDailyReports)),
      ]);
      setComplaints(complaintResult.data.items);
      setReports(reportResult.data.items);
      setDailyReports(dailyResult.data.items);
      const fallback = [complaintResult, reportResult, dailyResult].find((item) => item.source === "fallback");
      setSource(fallback ? "fallback" : "api");
      setError(fallback?.error);
      setLoading(false);
    }
    load();
  }, []);

  useEffect(() => {
    const requestedTab = new URLSearchParams(window.location.search).get("tab") ?? "all";
    if (tabs.some((tab) => tab.id === requestedTab)) setActiveTab(requestedTab);
  }, []);

  const signals = useMemo<IntakeSignal[]>(() => {
    const complaintSignals = complaints.map((item) => ({
      id: `complaint-${item.id}`,
      tab: "complaints" as const,
      sourceType: item.source,
      summary: item.summary,
      issueCategory: item.issue_category,
      vendorId: item.vendor_id,
      vendorName: item.vendor_name,
      region: item.region,
      school: item.school,
      severity: item.severity_score,
      confidence: Math.round(item.source_confidence * 100),
      status: item.status,
      caseId: item.case_id,
      timestamp: item.created_at,
    }));
    const reportSignals = reports.map((item) => ({
      id: `report-${item.id}`,
      tab: "reports" as const,
      sourceType: item.reporter_type,
      summary: item.summary,
      issueCategory: "official report",
      vendorId: item.vendor_id,
      vendorName: item.vendor_name,
      region: item.region,
      school: item.school,
      severity: item.linked_risk_score,
      confidence: item.completeness_score,
      status: item.status,
      caseId: item.case_id,
      timestamp: item.submitted_at,
    }));
    const dailySignals = dailyReports.map((item) => ({
      id: `daily-${item.id}`,
      tab: "daily-reports" as const,
      sourceType: "Daily Vendor Report",
      summary: `${item.actual_menu} delivered against planned menu ${item.planned_menu}`,
      issueCategory: item.mismatch_indicator ? "menu mismatch" : item.cost_estimate.cost_anomaly_flag ? "cost anomaly" : "daily evidence",
      vendorId: item.vendor_id,
      vendorName: item.vendor_name,
      region: item.region,
      school: item.school,
      severity: item.cost_estimate.cost_anomaly_flag ? 82 : item.mismatch_indicator ? 70 : 45,
      confidence: item.document_complete ? 80 : 55,
      status: item.verification_status,
      caseId: item.case_id,
      timestamp: item.delivery_timestamp,
    }));
    return [...complaintSignals, ...reportSignals, ...dailySignals].sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp));
  }, [complaints, dailyReports, reports]);

  if (loading) return <LoadingState />;

  const visible = activeTab === "all" ? signals : signals.filter((item) => item.tab === activeTab);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Signal Inbox"
        description="Raw MBG oversight signals enter here before they are grouped into cases for evidence review, scoring, and ticket action."
        breadcrumbs={[{ label: "Command Center", href: "/" }, { label: "Signal Inbox" }]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Intake is not a final enforcement view. Public complaints, official reports, and daily vendor reports become actionable only after they are linked to a case, scored, reviewed, and audited.
      </HelperPanel>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile label="All Signals" value={String(signals.length)} />
        <MetricTile label="Complaints" value={String(complaints.length)} />
        <MetricTile label="Official Reports" value={String(reports.length)} />
        <MetricTile label="Daily Reports" value={String(dailyReports.length)} />
      </div>

      <div className="overflow-x-auto rounded-xl border border-border bg-surface-raised p-2">
        <div className="flex min-w-max gap-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`shrink-0 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.id ? "bg-brand-500 text-white" : "text-muted-foreground hover:bg-surface hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
        </div>
      </div>

      <section className="min-w-0 overflow-hidden rounded-xl border border-border bg-surface-raised">
        <div className="overflow-x-auto">
        <table className="min-w-[920px] w-full text-left text-sm">
          <thead className="border-b border-border bg-surface-overlay text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-3">Signal</th>
              <th className="px-4 py-3">Issue</th>
              <th className="px-4 py-3">Vendor / Region</th>
              <th className="px-4 py-3">Risk</th>
              <th className="px-4 py-3">Linked Case</th>
              <th className="px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((signal) => (
              <tr key={signal.id} className="border-b border-border hover:bg-surface">
                <td className="px-4 py-4">
                  <div className="flex items-start gap-3">
                    <SourceIcon source={signal.tab} />
                    <div>
                      <p className="line-clamp-2 break-words font-medium">{signal.summary}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {signal.sourceType} · {new Date(signal.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4">
                  <StatusBadge label={signal.issueCategory} />
                </td>
                <td className="px-4 py-4">
                  <EntityChip label={signal.vendorName} href={`/vendors/${signal.vendorId}`} tone="vendor" />
                  <p className="mt-2 break-words text-xs text-muted-foreground">{signal.school} · {signal.region}</p>
                </td>
                <td className="px-4 py-4">
                  <p className="font-semibold">S {signal.severity}</p>
                  <p className="text-xs text-muted-foreground">C {signal.confidence}%</p>
                </td>
                <td className="px-4 py-4">
                  <EntityChip label={signal.caseId} href={`/cases/${signal.caseId}`} tone="case" />
                  <div className="mt-2"><StatusBadge label={signal.status} /></div>
                </td>
                <td className="px-4 py-4">
                  {signal.caseId ? (
                    <Link href={`/cases/${signal.caseId}`} className="rounded-md bg-brand-500 px-3 py-2 text-xs font-medium text-white hover:bg-brand-400">
                      Open Case
                    </Link>
                  ) : (
                    <button className="rounded-md border border-border px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-surface">
                      Create Case
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </section>
    </div>
  );
}

function SourceIcon({ source }: { source: IntakeSignal["tab"] }) {
  const Icon = source === "complaints" ? MessageSquareWarning : source === "reports" ? FileText : ClipboardList;
  return <Icon className="mt-0.5 h-4 w-4 shrink-0 text-brand-300" />;
}
