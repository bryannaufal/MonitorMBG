"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { asList, fallbackDailyReports, fallbackNutritionSummary } from "@/lib/demoFallback";
import type { DailyReport, ListResponse, NutritionSummary } from "@/types/monitoring";

export default function NutritionPage() {
  const [summary, setSummary] = useState<NutritionSummary | null>(null);
  const [reports, setReports] = useState<DailyReport[]>([]);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const [summaryResult, reportsResult] = await Promise.all([
        getWithFallback<NutritionSummary>("/nutrition/summary", fallbackNutritionSummary),
        getWithFallback<ListResponse<DailyReport>>("/daily-reports?size=100", asList(fallbackDailyReports)),
      ]);
      setSummary(summaryResult.data);
      setReports(reportsResult.data.items);
      const fallback = summaryResult.source === "fallback" ? summaryResult : reportsResult.source === "fallback" ? reportsResult : undefined;
      setSource(fallback ? "fallback" : "api");
      setError(fallback?.error);
      setLoading(false);
    }
    load();
  }, []);

  if (loading || !summary) return <LoadingState />;

  const flagged = reports.filter((item) => item.mismatch_indicator || item.duplicate_indicator || item.cost_estimate.cost_anomaly_flag || item.nutrition_estimate.protein_g < 15);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Nutrition & Cost Intelligence"
        description="Menu quality and budget plausibility signals connected to cases, vendors, evidence, and follow-up actions."
        breadcrumbs={[{ label: "Command Center", href: "/" }, { label: "Nutrition & Cost" }]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Nutrition and cost anomalies are not final violations. They are pre-verification signals that affect case priority and help operators decide whether to request clarification or schedule field verification.
      </HelperPanel>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
        <MetricTile label="Avg Calories" value={`${summary.avg_calories} kcal`} />
        <MetricTile label="Avg Protein" value={`${summary.avg_protein_g} g`} />
        <MetricTile label="Flagged Reports" value={String(flagged.length)} />
        <MetricTile label="Cost Anomalies" value={String(reports.filter((item) => item.cost_estimate.cost_anomaly_flag).length)} />
        <MetricTile label="Menu Mismatch" value={String(reports.filter((item) => item.mismatch_indicator).length)} />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {reports.map((report) => {
          const lowProtein = report.nutrition_estimate.protein_g < 15;
          return (
            <article key={report.id} className="rounded-xl border border-border bg-surface-raised p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap gap-2">
                    <EntityChip label={report.case_id} href={`/cases/${report.case_id}?tab=scoring`} tone="case" />
                    <EntityChip label={report.vendor_name} href={`/vendors/${report.vendor_id}`} tone="vendor" />
                  </div>
                  <h2 className="mt-3 text-lg font-semibold">{report.school}</h2>
                  <p className="text-sm text-muted-foreground">{report.region} · {report.actual_menu}</p>
                </div>
                <StatusBadge label={report.cost_estimate.cost_anomaly_flag ? "Cost Anomaly" : lowProtein ? "Low Protein Estimate" : "Needs Verification"} />
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-5">
                <Summary label="Calories" value={`${report.nutrition_estimate.calories}`} />
                <Summary label="Protein" value={`${report.nutrition_estimate.protein_g}g`} />
                <Summary label="Carbs" value={`${report.nutrition_estimate.carbs_g}g`} />
                <Summary label="Fat" value={`${report.nutrition_estimate.fat_g}g`} />
                <Summary label="Cost/Portion" value={`Rp ${report.cost_estimate.cost_per_portion.toLocaleString("id-ID")}`} />
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {report.mismatch_indicator ? <StatusBadge label="Menu Mismatch" /> : null}
                {lowProtein ? <StatusBadge label="Low Protein Estimate" /> : null}
                {report.cost_estimate.cost_anomaly_flag ? <StatusBadge label="Cost Anomaly" /> : null}
                {!report.document_complete ? <StatusBadge label="Documents Incomplete" /> : null}
              </div>
              <p className="mt-4 text-sm text-muted-foreground">{report.recommended_follow_up}</p>
              <Link href={`/cases/${report.case_id}?tab=scoring`} className="mt-4 inline-flex rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">
                Open Linked Case
              </Link>
            </article>
          );
        })}
      </div>
    </div>
  );
}

function Summary({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}
