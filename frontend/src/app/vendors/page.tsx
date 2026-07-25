"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { asList, fallbackCases, fallbackVendors } from "@/lib/demoFallback";
import type { ListResponse, OversightCase, Vendor } from "@/types/monitoring";

export default function VendorsPage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const result = await getWithFallback<ListResponse<Vendor>>("/vendors", asList(fallbackVendors));
      setVendors(result.data.items);
      setSource(result.source);
      setError(result.error);
      setLoading(false);
    }
    load();
  }, []);

  if (loading) return <LoadingState />;

  const watchlist = vendors.filter((vendor) => vendor.watchlist_status !== "Rendah");

  return (
    <div className="space-y-6">
      <PageHeader
        title="Daftar Pantauan Vendor"
        description="Profil risiko SPPG/vendor yang menunjukkan apakah kasus saat ini kejadian sekali atau pola pengawasan berulang."
        breadcrumbs={[{ label: "Pusat Kendali", href: "/" }, { label: "Daftar Pantauan Vendor" }]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Pembelajaran risiko vendor menghimpun aduan, laporan, bukti harian, tiket, hasil penilaian, dan catatan audit dari kasus dari waktu ke waktu.
      </HelperPanel>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile label="Total Vendor" value={String(vendors.length)} />
        <MetricTile label="Dalam Pantauan" value={String(watchlist.length)} />
        <MetricTile label="Kritis" value={String(vendors.filter((vendor) => vendor.watchlist_status === "Kritis").length)} />
        <MetricTile label="Porsi Tercakup" value={vendors.reduce((sum, vendor) => sum + vendor.daily_meal_volume, 0).toLocaleString("id-ID")} />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {vendors.map((vendor) => {
          const vendorCases = getVendorCases(vendor, source);
          const latestCase = vendorCases[0];
          return (
            <article key={vendor.id} className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <h2 className="break-words text-lg font-semibold">{vendor.name}</h2>
                  <p className="break-words text-sm text-muted-foreground">{vendor.district}, {vendor.region}</p>
                </div>
                <StatusBadge label={vendor.watchlist_status} />
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-5">
                <Metric label="Skor Risiko" value={String(vendor.risk_score)} />
                <Metric label="Porsi/hari" value={vendor.daily_meal_volume.toLocaleString("id-ID")} />
                <Metric label="Sekolah" value={String(vendor.assigned_schools.length)} />
                <Metric label="Isu Berulang" value={String(vendor.repeated_issue_categories.length)} />
                <Metric label="Kasus" value={String(vendorCases.length)} />
              </div>
              <p className="mt-4 break-words text-sm text-muted-foreground">{vendor.watchlist_reason}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {vendor.repeated_issue_categories.map((issue) => <StatusBadge key={issue} label={issue} />)}
              </div>
              <div className="mt-4 break-words rounded-lg border border-border bg-surface p-3 text-sm text-muted-foreground">
                Kasus terbaru: {latestCase ? <EntityChip label={latestCase.case_number} href={`/cases/${latestCase.case_id}`} tone="case" /> : noLinkedCaseMessage(source)}
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <Link href={`/vendors/${vendor.id}`} className="rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">
                  Buka Profil Vendor
                </Link>
                {latestCase ? (
                  <Link href={`/cases/${latestCase.case_id}`} className="rounded-md border border-border px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-surface">
                    Buka Kasus Terbaru
                  </Link>
                ) : null}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

function getVendorCases(vendor: Vendor, source: "api" | "fallback") {
  if (source === "api") {
    return sortByLatestUpdate(vendor.cases ?? []);
  }

  return sortByLatestUpdate(fallbackCases.filter((item) => item.vendor_id === vendor.id));
}

function sortByLatestUpdate(cases: OversightCase[]) {
  return [...cases].sort((a, b) => timestampForCase(b) - timestampForCase(a));
}

function timestampForCase(item: OversightCase) {
  const timestamp = Date.parse(item.updated_at || item.created_at);
  return Number.isFinite(timestamp) ? timestamp : 0;
}

function noLinkedCaseMessage(source: "api" | "fallback") {
  return source === "api"
    ? "Tidak ada kasus aktif dari daftar API. Buka profil vendor untuk riwayat kasus lengkap."
    : "Tidak ada kasus aktif pada data demo lokal.";
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg bg-surface p-3">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 break-words text-sm font-semibold">{value}</p>
    </div>
  );
}
