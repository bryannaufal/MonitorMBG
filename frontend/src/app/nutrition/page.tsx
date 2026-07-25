"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { asList, fallbackDailyReports, fallbackNutritionSummary } from "@/lib/demoFallback";
import { caseNumber } from "@/lib/utils";
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
        title="Gizi & Biaya"
        description="Sinyal kualitas menu dan kewajaran anggaran yang terhubung ke kasus, vendor, bukti, dan tindak lanjut."
        breadcrumbs={[{ label: "Pusat Kendali", href: "/" }, { label: "Gizi & Biaya" }]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Anomali gizi dan biaya bukan pelanggaran final. Ini sinyal pra-verifikasi yang memengaruhi prioritas kasus dan membantu operator memutuskan apakah perlu meminta klarifikasi atau menjadwalkan verifikasi lapangan.
      </HelperPanel>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <MetricTile label="Rata-rata Kalori" value={`${summary.avg_calories} kkal`} />
        <MetricTile label="Rata-rata Protein" value={`${summary.avg_protein_g} g`} />
        <MetricTile label="Laporan Ditandai" value={String(flagged.length)} />
        <MetricTile label="Anomali Biaya" value={String(reports.filter((item) => item.cost_estimate.cost_anomaly_flag).length)} />
        <MetricTile label="Ketidaksesuaian Menu" value={String(reports.filter((item) => item.mismatch_indicator).length)} />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {reports.map((report) => {
          const lowProtein = report.nutrition_estimate.protein_g < 15;
          return (
            <article key={report.id} className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap gap-2">
                    <EntityChip label={caseNumber(report.case_id)} href={`/cases/${report.case_id}`} tone="case" />
                    <EntityChip label={report.vendor_name} href={`/vendors/${report.vendor_id}`} tone="vendor" />
                  </div>
                  <h2 className="mt-3 break-words text-lg font-semibold">{report.school}</h2>
                  <p className="break-words text-sm text-muted-foreground">{report.region} · {report.actual_menu}</p>
                </div>
                <StatusBadge label={report.cost_estimate.cost_anomaly_flag ? "Anomali Biaya" : lowProtein ? "Estimasi Protein Rendah" : "Perlu Verifikasi"} />
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-5">
                <Summary label="Kalori" value={`${report.nutrition_estimate.calories}`} />
                <Summary label="Protein" value={`${report.nutrition_estimate.protein_g}g`} />
                <Summary label="Karbohidrat" value={`${report.nutrition_estimate.carbs_g}g`} />
                <Summary label="Lemak" value={`${report.nutrition_estimate.fat_g}g`} />
                <Summary label="Biaya/Porsi" value={`Rp ${report.cost_estimate.cost_per_portion.toLocaleString("id-ID")}`} />
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {report.mismatch_indicator ? <StatusBadge label="Ketidaksesuaian Menu" /> : null}
                {lowProtein ? <StatusBadge label="Estimasi Protein Rendah" /> : null}
                {report.cost_estimate.cost_anomaly_flag ? <StatusBadge label="Anomali Biaya" /> : null}
                {!report.document_complete ? <StatusBadge label="Dokumen Belum Lengkap" /> : null}
              </div>
              <p className="mt-4 break-words text-sm text-muted-foreground">{report.recommended_follow_up}</p>
              <Link href={`/cases/${report.case_id}`} className="mt-4 inline-flex rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">
                Buka Kasus Terkait
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
    <div className="min-w-0 rounded-lg border border-border bg-surface p-4">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 break-words text-base font-semibold sm:text-lg">{value}</p>
    </div>
  );
}
