"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import GiziBar from "@/components/monitoring/GiziBar";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { fallbackScores } from "@/lib/demoFallback";
import { fmtGizi, fmtScore, normalizeScore } from "@/lib/scoreDisplay";
import { caseNumber } from "@/lib/utils";
import type { ScoreResult } from "@/types/monitoring";

function fmtGiziCell(value: number | null | undefined): string {
  return fmtGizi(value);
}

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
      setScores(result.data.items.map(normalizeScore));
      setSelected(result.data.items[0] ? normalizeScore(result.data.items[0]) : null);
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
        title="Penilaian Risiko"
        description="Dampak, keyakinan, dapat ditindak, dan gizi — pra-verifikasi."
        breadcrumbs={[{ label: "Pusat Kendali", href: "/" }, { label: "Penilaian Risiko" }]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Skor akhir = 50% dampak + 25% keyakinan + 25% dapat ditindak. GIZI terpisah — strip (—) bila belum dinilai.
      </HelperPanel>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile label="Kasus Terperingkat" value={String(scores.length)} />
        <MetricTile label="Kritis/Tinggi" value={String(scores.filter((item) => ["Kritis", "Tinggi"].includes(item.priority_label)).length)} />
        <MetricTile label="Skor Tertinggi" value={String(scores[0]?.final_priority_score ?? 0)} />
        <MetricTile label="Rata-rata Keyakinan" value={`${Math.round(scores.reduce((sum, item) => sum + item.confidence_score, 0) / Math.max(1, scores.length))}`} />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <section className="min-w-0 overflow-hidden rounded-xl border border-border bg-surface-raised xl:col-span-2">
          <div className="overflow-x-auto">
            <table className="min-w-[880px] w-full text-left text-sm">
              <thead className="border-b border-border bg-surface-overlay text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">Kasus</th>
                  <th className="px-4 py-3">Dampak</th>
                  <th className="px-4 py-3">Keyakinan</th>
                  <th className="px-4 py-3">Dapat ditindak</th>
                  <th className="px-4 py-3">Gizi</th>
                  <th className="px-4 py-3">Akhir</th>
                </tr>
              </thead>
              <tbody>
                {scores.map((score) => (
                  <tr key={score.id} onClick={() => setSelected(normalizeScore(score))} className="cursor-pointer border-b border-border hover:bg-surface">
                    <td className="px-4 py-4">
                      <p className="break-words font-medium">{score.vendor_name}</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        <EntityChip label={caseNumber(score.case_id)} href={`/cases/${score.case_id}`} tone="case" />
                        <EntityChip label={score.region} />
                      </div>
                    </td>
                    <td className="px-4 py-4">{fmtScore(score.severity_score)}</td>
                    <td className="px-4 py-4">{fmtScore(score.confidence_score)}</td>
                    <td className="px-4 py-4">{fmtScore(score.actionability_score)}</td>
                    <td className="px-4 py-4 text-muted-foreground">{fmtGiziCell(score.nutrition_score)}</td>
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
          <h2 className="text-lg font-semibold">Penjelasan Skor</h2>
          {selected ? (
            <div className="mt-4 space-y-4">
              <div className="rounded-lg bg-surface p-4">
                <p className="text-sm text-muted-foreground">Skor Akhir</p>
                <p className="mt-1 text-3xl font-bold">{selected.final_priority_score}</p>
                <div className="mt-2"><StatusBadge label={selected.priority_label} /></div>
              </div>
              <div className="grid grid-cols-1 gap-3">
                <ScoreBar label="DAMPAK" value={selected.severity_score ?? 0} />
                <ScoreBar label="KEYAKINAN" value={selected.confidence_score ?? 0} />
                <ScoreBar label="DAPAT DITINDAK" value={selected.actionability_score ?? 0} />
                <GiziBar value={selected.nutrition_score} />
              </div>
              <p className="break-words text-sm leading-6 text-muted-foreground">{selected.explanation}</p>
              <div>
                <p className="text-sm font-medium">Rekomendasi Tindakan</p>
                <p className="mt-2 break-words text-sm text-muted-foreground">{selected.recommended_action}</p>
              </div>
              <Link href={`/cases/${selected.case_id}`} className="inline-flex rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">
                Buka Kasus
              </Link>
            </div>
          ) : (
            <p className="mt-4 text-sm text-muted-foreground">Pilih salah satu hasil penilaian.</p>
          )}
        </aside>
      </div>
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{value}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-surface-overlay">
        <div className="h-full rounded-full bg-brand-400" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
      </div>
    </div>
  );
}
