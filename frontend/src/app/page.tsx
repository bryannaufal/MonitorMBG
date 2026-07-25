"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertTriangle, ArrowRight, Clock, RadioTower, ShieldAlert } from "lucide-react";

import StatsCard from "@/components/dashboard/StatsCard";
import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { caseNumber } from "@/lib/utils";
import {
  asList,
  fallbackAnomalies,
  fallbackCases,
  fallbackComplaints,
  fallbackHeatmap,
  fallbackOverview,
  fallbackVendors,
} from "@/lib/demoFallback";
import type {
  AnalyticsOverview,
  AnomalyHighlight,
  Complaint,
  HeatmapRegion,
  ListResponse,
  OversightCase,
  Vendor,
} from "@/types/monitoring";

interface DashboardState {
  overview: AnalyticsOverview;
  heatmap: HeatmapRegion[];
  anomalies: AnomalyHighlight[];
  vendors: Vendor[];
  cases: OversightCase[];
  complaints: Complaint[];
}

export default function DashboardHome() {
  const [data, setData] = useState<DashboardState | null>(null);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();

  useEffect(() => {
    async function load() {
      const [overview, heatmap, anomalies, vendors, casesResult, complaints] = await Promise.all([
        getWithFallback<AnalyticsOverview>("/analytics/overview", fallbackOverview),
        getWithFallback<{ regions: HeatmapRegion[] }>("/analytics/heatmap", { regions: fallbackHeatmap }),
        getWithFallback<{ anomalies: AnomalyHighlight[] }>("/analytics/anomalies", { anomalies: fallbackAnomalies }),
        getWithFallback<ListResponse<Vendor>>("/vendors", asList(fallbackVendors)),
        getWithFallback<ListResponse<OversightCase>>("/cases", asList(fallbackCases)),
        getWithFallback<ListResponse<Complaint>>("/complaints?size=6", asList(fallbackComplaints)),
      ]);
      const fallback = [overview, heatmap, anomalies, vendors, casesResult, complaints].find((item) => item.source === "fallback");
      setSource(fallback ? "fallback" : "api");
      setError(fallback?.error);
      setData({
        overview: overview.data,
        heatmap: heatmap.data.regions,
        anomalies: anomalies.data.anomalies,
        vendors: vendors.data.items,
        cases: casesResult.data.items,
        complaints: complaints.data.items,
      });
    }
    load();
  }, []);

  if (!data) return <LoadingState />;

  const priorityCases = data.cases.slice(0, 5);
  const watchlist = data.vendors.filter((vendor) => ["Kritis", "Tinggi", "Critical", "High"].includes(vendor.watchlist_status)).slice(0, 4);
  const activeCases = data.cases.filter((item) => item.status !== "Selesai").length;
  const incomingSignals = data.overview.public_signals;
  const recentSignals = data.complaints.filter((c) => c.case_id);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Pusat Kendali"
        description="Titik awal harian pengawasan MBG nasional: pantau situasi, buka kasus berisiko tinggi, dan dorong tindak lanjut tiket yang akuntabel."
        breadcrumbs={[{ label: "Pusat Kendali" }]}
        source={source}
        error={error}
      />
      <GovernanceNote />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-6">
        <StatsCard title="Kasus Aktif" value={String(activeCases)} trend="Antrean kasus" />
        <StatsCard title="Kritis/Tinggi" value={String(data.overview.high_risk_cases)} trend="+3" />
        <StatsCard title="Sinyal Masuk" value={String(incomingSignals)} trend={data.overview.public_signal_spike} />
        <StatsCard title="Rata-rata Waktu Triase" value={data.overview.average_triage_time} trend="-4 jam" />
        <StatsCard title="Respons Tiket" value={`${data.overview.ticket_response_rate}%`} trend="+6%" />
        <StatsCard title="Daftar Pantauan" value={String(data.overview.vendors_on_watchlist)} trend="Vendor" />
      </div>

      <HelperPanel>
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <span>
            Alur demo yang disarankan: Kotak Masuk Sinyal {"->"} Buka Kasus {"->"} Bukti & Verifikasi {"->"} Penilaian Risiko {"->"} Tiket Tindak Lanjut {"->"} Jejak Audit.
          </span>
          <Link href="/intake" className="inline-flex shrink-0 items-center gap-2 rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">
            Mulai dari Sinyal <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </HelperPanel>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5 xl:col-span-2">
          <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <h2 className="text-lg font-semibold">Antrean Kerja Prioritas</h2>
              <p className="text-sm text-muted-foreground">Kasus teratas yang memerlukan perhatian operator sekarang.</p>
            </div>
            <Link href="/cases" className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm text-muted-foreground hover:bg-surface">
              Lihat Kasus <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="space-y-3">
            {priorityCases.map((item) => (
              <article key={item.case_id} className="min-w-0 rounded-lg border border-border bg-surface p-4">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap gap-2">
                      <EntityChip label={item.case_number} href={`/cases/${item.case_id}`} tone="case" />
                      <StatusBadge label={item.priority_label} />
                      <StatusBadge label={item.status} />
                    </div>
                    <h3 className="mt-2 break-words font-semibold">{item.title}</h3>
                    <p className="mt-1 break-words text-sm text-muted-foreground">{item.vendor_name} · {item.region} · {item.sla_status}</p>
                    <p className="mt-2 break-words text-sm text-muted-foreground">{item.recommended_action}</p>
                  </div>
                  <Link href={`/cases/${item.case_id}`} className="inline-flex shrink-0 justify-center rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">
                    Buka Kasus
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
          <div className="mb-4 flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-red-300" />
            <h2 className="text-lg font-semibold">Pratinjau Daftar Pantauan Vendor</h2>
          </div>
          <div className="space-y-3">
            {watchlist.map((vendor) => (
              <Link key={vendor.id} href={`/vendors/${vendor.id}`} className="block min-w-0 rounded-lg border border-border bg-surface p-4 transition-colors hover:border-brand-500/60">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <p className="break-words font-medium">{vendor.name}</p>
                    <p className="break-words text-xs text-muted-foreground">{vendor.district}, {vendor.region}</p>
                  </div>
                  <StatusBadge label={vendor.watchlist_status} />
                </div>
                <p className="mt-2 break-words text-sm text-muted-foreground">{vendor.watchlist_reason}</p>
                <p className="mt-3 text-sm font-semibold text-brand-300">Skor risiko {vendor.risk_score}</p>
              </Link>
            ))}
          </div>
        </section>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
          <div className="mb-4 flex items-center gap-2">
            <RadioTower className="h-5 w-5 text-brand-300" />
            <h2 className="text-lg font-semibold">Panel Situasi Wilayah</h2>
          </div>
          <div className="space-y-3">
            {data.heatmap.slice(0, 4).map((region) => (
              <Link key={`${region.region}-${region.district}`} href="/heatmap" className="block rounded-lg border border-border bg-surface p-4 hover:border-brand-500/60">
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="break-words font-medium">{region.region}</p>
                    <p className="break-words text-xs text-muted-foreground">{region.district}</p>
                  </div>
                  <StatusBadge label={region.risk_score >= 80 ? "Kritis" : region.risk_score >= 65 ? "Tinggi" : "Sedang"} />
                </div>
                <div className="mt-3 h-2 rounded-full bg-surface-overlay">
                  <div className="h-2 rounded-full bg-brand-500" style={{ width: `${region.risk_score}%` }} />
                </div>
              </Link>
            ))}
          </div>
        </section>

        <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
          <div className="mb-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-300" />
            <h2 className="text-lg font-semibold">Peringatan Anomali Aktif</h2>
          </div>
          <div className="space-y-3">
            {data.anomalies.map((anomaly) => (
              <div key={anomaly.id} className="rounded-lg border border-border bg-surface p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium">{anomaly.issue_category}</p>
                  <StatusBadge label={anomaly.severity} />
                </div>
                <p className="mt-2 break-words text-sm text-muted-foreground">{anomaly.description}</p>
                <p className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" /> {anomaly.region}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
          <h2 className="text-lg font-semibold">Sinyal Terbaru</h2>
          <div className="mt-4 space-y-3">
            {recentSignals.map((complaint) => (
              <Link key={complaint.id} href={`/cases/${complaint.case_id}`} className="block min-w-0 rounded-lg border border-border bg-surface p-4 hover:border-brand-500/60">
                <p className="break-words font-medium">{complaint.summary}</p>
                <p className="mt-1 break-words text-sm text-muted-foreground">{complaint.source} · {complaint.region}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <EntityChip label={caseNumber(complaint.case_id!)} tone="case" />
                  <EntityChip label={complaint.vendor_name} tone="vendor" />
                </div>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
