"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { fallbackCases, fallbackVendors } from "@/lib/demoFallback";
import type { Vendor } from "@/types/monitoring";

export default function VendorProfilePage() {
  const params = useParams<{ id: string }>();
  const fallback = fallbackVendors.find((vendor) => vendor.id === params.id) ?? fallbackVendors[0];
  const [vendor, setVendor] = useState<Vendor | null>(null);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const result = await getWithFallback<Vendor>(`/vendors/${params.id}`, fallback);
      setVendor(result.data);
      setSource(result.source);
      setError(result.error);
      setLoading(false);
    }
    load();
  }, [fallback, params.id]);

  const vendorCases = useMemo(() => {
    return vendor?.cases?.length ? vendor.cases : fallbackCases.filter((item) => item.vendor_id === params.id);
  }, [params.id, vendor?.cases]);

  if (loading || !vendor) return <LoadingState />;

  const complaints = vendor.linked_complaints ?? vendorCases.flatMap((item) => item.complaints);
  const reports = vendor.linked_reports ?? vendorCases.flatMap((item) => item.reports);
  const dailyReports = vendor.linked_daily_reports ?? vendor.nutrition_cost_anomalies ?? vendorCases.flatMap((item) => item.daily_reports);
  const tickets = vendor.ticket_history ?? vendorCases.flatMap((item) => (item.ticket ? [item.ticket] : []));
  const audit = vendor.audit_notes ?? vendorCases.flatMap((item) => item.audit_events);

  return (
    <div className="space-y-6">
      <PageHeader
        title={vendor.name}
        description="Vendor risk profile showing recurring patterns across linked cases, signals, evidence, tickets, and audit notes."
        breadcrumbs={[
          { label: "Vendor Watchlist", href: "/vendors" },
          { label: vendor.name },
        ]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Vendor profiles answer whether the current case is isolated or part of a repeated SPPG/vendor risk pattern that should change oversight intensity.
      </HelperPanel>

      <section className="rounded-xl border border-border bg-surface-raised p-5">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <StatusBadge label={vendor.watchlist_status} />
            <p className="mt-3 text-xl font-semibold">Risk Score {vendor.risk_score}</p>
            <p className="mt-2 max-w-3xl text-sm text-muted-foreground">{vendor.watchlist_reason}</p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
            <MetricTile label="Region" value={vendor.region} />
            <MetricTile label="Meals/day" value={vendor.daily_meal_volume.toLocaleString("id-ID")} />
            <MetricTile label="Schools" value={String(vendor.assigned_schools.length)} />
            <MetricTile label="Active Cases" value={String(vendorCases.filter((item) => item.status !== "Resolved").length)} />
          </div>
        </div>
        <div className="mt-5">
          <p className="text-sm font-medium">Risk Trend</p>
          <div className="mt-3 flex h-24 items-end gap-2 rounded-lg bg-surface p-3">
            {vendor.risk_trend.map((value, index) => (
              <div key={`${value}-${index}`} className="w-8 rounded-t bg-brand-500" style={{ height: `${value}%` }} title={`${value}`} />
            ))}
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
        <MetricTile label="Cases" value={String(vendorCases.length)} />
        <MetricTile label="Complaints" value={String(complaints.length)} />
        <MetricTile label="Reports" value={String(reports.length)} />
        <MetricTile label="Daily Reports" value={String(dailyReports.length)} />
        <MetricTile label="Tickets" value={String(tickets.length)} />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <section className="rounded-xl border border-border bg-surface-raised p-5 xl:col-span-2">
          <h2 className="text-lg font-semibold">Active & Historical Cases</h2>
          <div className="mt-4 space-y-3">
            {vendorCases.map((item) => (
              <Link key={item.case_id} href={`/cases/${item.case_id}`} className="block rounded-lg border border-border bg-surface p-4 hover:border-brand-500/60">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <EntityChip label={item.case_id} tone="case" />
                    <p className="mt-2 font-medium">{item.title}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{item.issue_category} · {item.region} · Score {item.score.final_priority_score}</p>
                  </div>
                  <StatusBadge label={item.priority_label} />
                </div>
              </Link>
            ))}
          </div>
        </section>

        <section className="rounded-xl border border-border bg-surface-raised p-5">
          <h2 className="text-lg font-semibold">Recommended Oversight Action</h2>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">{vendor.recommended_action}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {vendor.repeated_issue_categories.length ? vendor.repeated_issue_categories.map((issue) => <StatusBadge key={issue} label={issue} />) : <StatusBadge label="Routine Monitoring" />}
          </div>
        </section>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Summary title="Linked Complaints" count={complaints.length} text={complaints[0]?.summary ?? "No linked public complaint in demo data."} />
        <Summary title="Nutrition/Cost History" count={dailyReports.length} text={dailyReports[0]?.recommended_follow_up ?? "No nutrition/cost anomaly in demo data."} />
        <Summary title="Audit Notes" count={audit.length} text={audit[0]?.description ?? "Audit notes appear when case actions are recorded."} />
      </div>
    </div>
  );
}

function Summary({ title, count, text }: { title: string; count: number; text: string }) {
  return (
    <section className="rounded-xl border border-border bg-surface-raised p-5">
      <p className="text-sm text-muted-foreground">{title}</p>
      <p className="mt-1 text-3xl font-bold">{count}</p>
      <p className="mt-3 text-sm text-muted-foreground">{text}</p>
    </section>
  );
}
