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
import { caseNumber } from "@/lib/utils";
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
        description="Profil risiko vendor yang menunjukkan pola berulang lintas kasus, sinyal, bukti, tiket, dan catatan audit terhubung."
        breadcrumbs={[
          { label: "Daftar Pantauan Vendor", href: "/vendors" },
          { label: vendor.name },
        ]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Profil vendor menjawab apakah kasus saat ini terisolasi atau bagian dari pola risiko SPPG/vendor berulang yang perlu mengubah intensitas pengawasan.
      </HelperPanel>

      <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="min-w-0">
            <StatusBadge label={vendor.watchlist_status} />
            <p className="mt-3 break-words text-xl font-semibold">Skor Risiko {vendor.risk_score}</p>
            <p className="mt-2 max-w-3xl break-words text-sm text-muted-foreground">{vendor.watchlist_reason}</p>
          </div>
          <div className="grid w-full grid-cols-1 gap-3 text-sm sm:grid-cols-2 lg:w-auto lg:grid-cols-4">
            <MetricTile label="Wilayah" value={vendor.region} />
            <MetricTile label="Porsi/hari" value={vendor.daily_meal_volume.toLocaleString("id-ID")} />
            <MetricTile label="Sekolah" value={String(vendor.assigned_schools.length)} />
            <MetricTile label="Kasus Aktif" value={String(vendorCases.filter((item) => item.status !== "Selesai").length)} />
          </div>
        </div>
        <div className="mt-5">
          <p className="text-sm font-medium">Tren Risiko</p>
          <div className="mt-3 flex h-24 items-end gap-2 rounded-lg bg-surface p-3">
            {vendor.risk_trend.map((value, index) => (
              <div key={`${value}-${index}`} className="w-8 rounded-t bg-brand-500" style={{ height: `${value}%` }} title={`${value}`} />
            ))}
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <MetricTile label="Kasus" value={String(vendorCases.length)} />
        <MetricTile label="Aduan" value={String(complaints.length)} />
        <MetricTile label="Laporan" value={String(reports.length)} />
        <MetricTile label="Laporan Harian" value={String(dailyReports.length)} />
        <MetricTile label="Tiket" value={String(tickets.length)} />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5 xl:col-span-2">
          <h2 className="text-lg font-semibold">Kasus Aktif & Riwayat</h2>
          <div className="mt-4 space-y-3">
            {vendorCases.map((item) => (
              <Link key={item.case_id} href={`/cases/${item.case_id}`} className="block min-w-0 rounded-lg border border-border bg-surface p-4 hover:border-brand-500/60">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <EntityChip label={item.case_number ?? caseNumber(item.case_id)} tone="case" />
                    <p className="mt-2 break-words font-medium">{item.title}</p>
                    <p className="mt-1 break-words text-sm text-muted-foreground">{item.issue_category} · {item.region} · Skor {item.score.final_priority_score}</p>
                  </div>
                  <StatusBadge label={item.priority_label} />
                </div>
              </Link>
            ))}
          </div>
        </section>

        <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
          <h2 className="text-lg font-semibold">Rekomendasi Tindakan Pengawasan</h2>
          <p className="mt-3 break-words text-sm leading-6 text-muted-foreground">{vendor.recommended_action}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {vendor.repeated_issue_categories.length ? vendor.repeated_issue_categories.map((issue) => <StatusBadge key={issue} label={issue} />) : <StatusBadge label="Pemantauan Rutin" />}
          </div>
        </section>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Summary title="Aduan Terhubung" count={complaints.length} text={complaints[0]?.summary ?? "Tidak ada aduan publik terhubung pada data demo."} />
        <Summary title="Riwayat Gizi/Biaya" count={dailyReports.length} text={dailyReports[0]?.recommended_follow_up ?? "Tidak ada anomali gizi/biaya pada data demo."} />
        <Summary title="Catatan Audit" count={audit.length} text={audit[0]?.description ?? "Catatan audit muncul ketika tindakan kasus tercatat."} />
      </div>
    </div>
  );
}

function Summary({ title, count, text }: { title: string; count: number; text: string }) {
  return (
    <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
      <p className="text-sm text-muted-foreground">{title}</p>
      <p className="mt-1 text-3xl font-bold">{count}</p>
      <p className="mt-3 break-words text-sm text-muted-foreground">{text}</p>
    </section>
  );
}
