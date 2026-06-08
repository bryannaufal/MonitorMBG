"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Filter, Search } from "lucide-react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { asList, fallbackCases } from "@/lib/demoFallback";
import type { ListResponse, OversightCase } from "@/types/monitoring";

export default function CasesPage() {
  const [cases, setCases] = useState<OversightCase[]>([]);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [priority, setPriority] = useState("All");
  const [status, setStatus] = useState("All");
  const [region, setRegion] = useState("All");
  const [query, setQuery] = useState("");

  useEffect(() => {
    async function load() {
      const result = await getWithFallback<ListResponse<OversightCase>>("/cases", asList(fallbackCases));
      setCases(result.data.items);
      setSource(result.source);
      setError(result.error);
      setLoading(false);
    }
    load();
  }, []);

  useEffect(() => {
    const selectedRegion = new URLSearchParams(window.location.search).get("region");
    if (selectedRegion) setRegion(selectedRegion);
  }, []);

  const filtered = useMemo(() => {
    return cases.filter((item) => {
      const haystack = `${item.title} ${item.vendor_name} ${item.school} ${item.case_id} ${item.issue_category}`.toLowerCase();
      return (
        (priority === "All" || item.priority_label === priority) &&
        (status === "All" || item.status === status) &&
        (region === "All" || item.region === region) &&
        (!query || haystack.includes(query.toLowerCase()))
      );
    });
  }, [cases, priority, query, region, status]);

  if (loading) return <LoadingState />;

  const regions = Array.from(new Set(cases.map((item) => item.region)));
  const statuses = Array.from(new Set(cases.map((item) => item.status)));
  const highRisk = cases.filter((item) => ["Critical", "High"].includes(item.priority_label)).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Cases"
        description="Prioritized oversight cases generated from public signals, reports, daily vendor evidence, and risk scoring."
        breadcrumbs={[{ label: "Command Center", href: "/" }, { label: "Cases" }]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Cases are the center of MonitorMBG. Every signal, evidence item, score, ticket, vendor pattern, copilot answer, and audit event is connected back to a case.
      </HelperPanel>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile label="Active Cases" value={String(cases.length)} detail="Generated from linked intake records" />
        <MetricTile label="Critical/High" value={String(highRisk)} detail="Requires near-term review" />
        <MetricTile label="Evidence Items" value={String(cases.reduce((sum, item) => sum + item.evidence_count, 0))} detail="Attached to cases" />
        <MetricTile label="Open Tickets" value={String(cases.filter((item) => item.ticket && item.ticket.status !== "Resolved").length)} detail="Action layer" />
      </div>

      <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
          <div className="relative min-w-0 flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search case, vendor, school, issue..."
              className="h-9 w-full rounded-md border border-border bg-surface pl-9 pr-3 text-sm outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 xl:flex xl:shrink-0">
            <FilterSelect label="Priority" value={priority} options={["All", "Critical", "High", "Medium", "Low"]} onChange={setPriority} />
            <FilterSelect label="Status" value={status} options={["All", ...statuses]} onChange={setStatus} />
            <FilterSelect label="Region" value={region} options={["All", ...regions]} onChange={setRegion} />
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {filtered.map((item) => (
          <article key={item.case_id} className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap gap-2">
                  <EntityChip label={item.case_id} href={`/cases/${item.case_id}`} tone="case" />
                  <EntityChip label={item.vendor_name} href={`/vendors/${item.vendor_id}`} tone="vendor" />
                  {item.ticket_id ? <EntityChip label={item.ticket_id} tone="ticket" /> : null}
                </div>
                <h2 className="mt-3 break-words text-lg font-semibold">{item.title}</h2>
                <p className="mt-1 break-words text-sm text-muted-foreground">
                  {item.school} · {item.district}, {item.region} · {item.issue_category}
                </p>
              </div>
              <div className="flex shrink-0 flex-row flex-wrap gap-2 sm:flex-col sm:items-end">
                <StatusBadge label={item.priority_label} />
                <StatusBadge label={item.status} />
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-5">
              <Mini label="Severity" value={String(item.score.severity_score)} />
              <Mini label="Confidence" value={String(item.score.confidence_score)} />
              <Mini label="Final" value={String(item.score.final_priority_score)} />
              <Mini label="Signals" value={String(item.signals_count)} />
              <Mini label="SLA" value={item.sla_status} />
            </div>

            <p className="mt-4 break-words text-sm leading-6 text-muted-foreground">{item.recommended_action}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link href={`/cases/${item.case_id}`} className="inline-flex justify-center rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-400">
                Open Case
              </Link>
              <Link href={`/cases/${item.case_id}?tab=scoring`} className="inline-flex justify-center rounded-md border border-border px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-surface">
                Explain Score
              </Link>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="flex min-w-0 items-center gap-2 text-sm text-muted-foreground">
      <span className="hidden items-center gap-1 lg:inline-flex">
        <Filter className="h-3.5 w-3.5" />
        {label}
      </span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-9 w-full min-w-0 rounded-md border border-border bg-surface px-3 text-sm text-foreground outline-none focus:ring-1 focus:ring-brand-500"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg bg-surface p-3">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 break-words text-sm font-semibold">{value}</p>
    </div>
  );
}
