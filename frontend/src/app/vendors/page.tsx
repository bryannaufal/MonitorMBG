"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { asList, fallbackCases, fallbackVendors } from "@/lib/demoFallback";
import type { ListResponse, Vendor } from "@/types/monitoring";

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

  const watchlist = vendors.filter((vendor) => vendor.watchlist_status !== "Low");

  return (
    <div className="space-y-6">
      <PageHeader
        title="Vendor Watchlist"
        description="SPPG/vendor risk profiles showing whether current cases are one-time events or recurring oversight patterns."
        breadcrumbs={[{ label: "Command Center", href: "/" }, { label: "Vendor Watchlist" }]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Vendor risk learning accumulates linked complaints, reports, daily evidence, tickets, scoring outcomes, and audit notes from cases over time.
      </HelperPanel>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile label="Vendors" value={String(vendors.length)} />
        <MetricTile label="Watchlist" value={String(watchlist.length)} />
        <MetricTile label="Critical" value={String(vendors.filter((vendor) => vendor.watchlist_status === "Critical").length)} />
        <MetricTile label="Meals Covered" value={vendors.reduce((sum, vendor) => sum + vendor.daily_meal_volume, 0).toLocaleString("id-ID")} />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {vendors.map((vendor) => {
          const vendorCases = fallbackCases.filter((item) => item.vendor_id === vendor.id);
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
                <Metric label="Risk" value={String(vendor.risk_score)} />
                <Metric label="Meals/day" value={vendor.daily_meal_volume.toLocaleString("id-ID")} />
                <Metric label="Schools" value={String(vendor.assigned_schools.length)} />
                <Metric label="Issues" value={String(vendor.repeated_issue_categories.length)} />
                <Metric label="Cases" value={String(vendorCases.length)} />
              </div>
              <p className="mt-4 break-words text-sm text-muted-foreground">{vendor.watchlist_reason}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {vendor.repeated_issue_categories.map((issue) => <StatusBadge key={issue} label={issue} />)}
              </div>
              <div className="mt-4 break-words rounded-lg border border-border bg-surface p-3 text-sm text-muted-foreground">
                Latest case: {latestCase ? <EntityChip label={latestCase.case_id} href={`/cases/${latestCase.case_id}`} tone="case" /> : "No active linked case in fallback data"}
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <Link href={`/vendors/${vendor.id}`} className="rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">
                  Open Vendor Profile
                </Link>
                {latestCase ? (
                  <Link href={`/cases/${latestCase.case_id}`} className="rounded-md border border-border px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-surface">
                    Open Latest Case
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

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg bg-surface p-3">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 break-words text-sm font-semibold">{value}</p>
    </div>
  );
}
