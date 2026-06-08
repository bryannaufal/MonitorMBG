"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { fallbackScores } from "@/lib/demoFallback";
import type { ScoreResult } from "@/types/monitoring";

export default function ScoringPage() {
  const [scores, setScores] = useState<ScoreResult[]>([]);
  const [selected, setSelected] = useState<ScoreResult | null>(null);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const result = await getWithFallback<{ items: ScoreResult[]; total: number }>("/scoring/rankings", {
        items: fallbackScores,
        total: fallbackScores.length,
      });
      setScores(result.data.items);
      setSelected(result.data.items[0] ?? null);
      setSource(result.source);
      setError(result.error);
      setLoading(false);
    }
    load();
  }, []);

  if (loading) return <LoadingState />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Risk Prioritization"
        description="Explainable case ranking that combines severity, confidence, nutrition, cost, anomaly, and evidence completeness signals."
        breadcrumbs={[{ label: "Command Center", href: "/" }, { label: "Risk Prioritization" }]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Risk scoring combines severity, confidence, nutrition, cost, anomaly, and evidence completeness into a prioritization signal. Operators remain responsible for final decisions.
      </HelperPanel>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile label="Ranked Cases" value={String(scores.length)} />
        <MetricTile label="Critical/High" value={String(scores.filter((item) => ["Critical", "High"].includes(item.priority_label)).length)} />
        <MetricTile label="Top Score" value={String(scores[0]?.final_priority_score ?? 0)} />
        <MetricTile label="Avg Confidence" value={`${Math.round(scores.reduce((sum, item) => sum + item.confidence_score, 0) / Math.max(1, scores.length))}%`} />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <section className="min-w-0 overflow-hidden rounded-xl border border-border bg-surface-raised xl:col-span-2">
          <div className="overflow-x-auto">
          <table className="min-w-[840px] w-full text-left text-sm">
            <thead className="border-b border-border bg-surface-overlay text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-4 py-3">Ranked Case</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3">Nutrition</th>
                <th className="px-4 py-3">Cost</th>
                <th className="px-4 py-3">Anomaly</th>
                <th className="px-4 py-3">Final</th>
              </tr>
            </thead>
            <tbody>
              {scores.map((score) => (
                <tr key={score.id} onClick={() => setSelected(score)} className="cursor-pointer border-b border-border hover:bg-surface">
                  <td className="px-4 py-4">
                    <p className="break-words font-medium">{score.vendor_name}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <EntityChip label={score.case_id} href={`/cases/${score.case_id}?tab=scoring`} tone="case" />
                      <EntityChip label={score.region} />
                    </div>
                  </td>
                  <td className="px-4 py-4">{score.severity_score}</td>
                  <td className="px-4 py-4">{score.confidence_score}</td>
                  <td className="px-4 py-4">{score.nutrition_concern_score}</td>
                  <td className="px-4 py-4">{score.cost_anomaly_score}</td>
                  <td className="px-4 py-4">{score.anomaly_score}</td>
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-semibold">{score.final_priority_score}</span>
                      <StatusBadge label={score.priority_label} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </section>

        <aside className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
          <h2 className="text-lg font-semibold">Score Explanation</h2>
          {selected ? (
            <div className="mt-4 space-y-4">
              <div className="rounded-lg bg-surface p-4">
                <p className="text-sm text-muted-foreground">Final Priority</p>
                <p className="mt-1 text-3xl font-bold">{selected.final_priority_score}</p>
                <div className="mt-2"><StatusBadge label={selected.priority_label} /></div>
              </div>
              <p className="break-words text-sm leading-6 text-muted-foreground">{selected.explanation}</p>
              <div>
                <p className="text-sm font-medium">Recommended Action</p>
                <p className="mt-2 break-words text-sm text-muted-foreground">{selected.recommended_action}</p>
              </div>
              <Link href={`/cases/${selected.case_id}?tab=scoring`} className="inline-flex rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">
                Open Case Score
              </Link>
            </div>
          ) : (
            <p className="mt-4 text-sm text-muted-foreground">Select a scoring result.</p>
          )}
        </aside>
      </div>
    </div>
  );
}
