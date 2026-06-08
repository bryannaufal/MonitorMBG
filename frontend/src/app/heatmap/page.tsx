"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { fallbackAnomalies, fallbackHeatmap, fallbackVendors } from "@/lib/demoFallback";
import type { AnomalyHighlight, HeatmapRegion } from "@/types/monitoring";

export default function HeatmapPage() {
  const [regions, setRegions] = useState<HeatmapRegion[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyHighlight[]>([]);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const [heatmap, anomalyResult] = await Promise.all([
        getWithFallback<{ regions: HeatmapRegion[] }>("/analytics/heatmap", { regions: fallbackHeatmap }),
        getWithFallback<{ anomalies: AnomalyHighlight[] }>("/analytics/anomalies", { anomalies: fallbackAnomalies }),
      ]);
      setRegions([...heatmap.data.regions].sort((a, b) => b.risk_score - a.risk_score));
      setAnomalies(anomalyResult.data.anomalies);
      const fallback = heatmap.source === "fallback" ? heatmap : anomalyResult.source === "fallback" ? anomalyResult : undefined;
      setSource(fallback ? "fallback" : "api");
      setError(fallback?.error);
      setLoading(false);
    }
    load();
  }, []);

  if (loading) return <LoadingState />;

  const top = regions[0];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Regional Risk Intelligence"
        description="Ranked regional oversight view showing where complaints, high-risk cases, and anomaly patterns are concentrated."
        breadcrumbs={[{ label: "Command Center", href: "/" }, { label: "Regional Heatmap" }]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Regional risk is a prioritization signal for supervision planning. Operators should open linked cases before taking field or vendor actions.
      </HelperPanel>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile label="Highest Region" value={top?.region ?? "N/A"} detail={top ? `Risk ${top.risk_score}` : undefined} />
        <MetricTile label="Regions Ranked" value={String(regions.length)} />
        <MetricTile label="Complaint Signals" value={String(regions.reduce((sum, item) => sum + item.complaint_count, 0))} />
        <MetricTile label="High-Risk Cases" value={String(regions.reduce((sum, item) => sum + item.high_priority_cases, 0))} />
      </div>

      <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
        <h2 className="text-lg font-semibold">Region Risk Ranking</h2>
        <div className="mt-4 space-y-3">
          {regions.map((region, index) => {
            const anomaly = anomalies.find((item) => item.region === region.region);
            const vendor = fallbackVendors.find((item) => item.region === region.region || item.district === region.district);
            return (
              <article key={`${region.region}-${region.district}`} className="min-w-0 rounded-lg border border-border bg-surface p-4">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-sm text-brand-300">#{index + 1}</span>
                      <h3 className="break-words font-semibold">{region.region}</h3>
                      <StatusBadge label={region.risk_score >= 80 ? "Critical" : region.risk_score >= 65 ? "High" : "Medium"} />
                    </div>
                    <p className="mt-1 break-words text-sm text-muted-foreground">
                      {region.district} · {region.complaint_count} signals · {region.high_priority_cases} high-risk cases
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <EntityChip label={anomaly?.issue_category ?? "dominant issue pending"} />
                      {vendor ? <EntityChip label={vendor.name} href={`/vendors/${vendor.id}`} tone="vendor" /> : null}
                    </div>
                  </div>
                  <div className="min-w-0 lg:w-64 lg:shrink-0">
                    <div className="h-2 rounded-full bg-surface-overlay">
                      <div className="h-2 rounded-full bg-brand-500" style={{ width: `${region.risk_score}%` }} />
                    </div>
                    <Link href={`/cases?region=${encodeURIComponent(region.region)}`} className="mt-3 inline-flex rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">
                      View Cases
                    </Link>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </section>
    </div>
  );
}
