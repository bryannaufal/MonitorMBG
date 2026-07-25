"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import CopilotPanel from "@/components/copilot/CopilotPanel";
import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { asList, fallbackCases } from "@/lib/demoFallback";
import { caseNumber } from "@/lib/utils";
import type { ListResponse, OversightCase } from "@/types/monitoring";

export default function CopilotPage() {
  const [cases, setCases] = useState<OversightCase[]>([]);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const result = await getWithFallback<ListResponse<OversightCase>>("/cases", asList(fallbackCases));
      setCases(result.data.items);
      setSource(result.source);
      setError(result.error);
      setLoading(false);
    }
    load();
  }, []);

  if (loading) return <LoadingState />;

  return (
    <div className="flex min-h-full flex-col space-y-6">
      <PageHeader
        title="Asisten Ringkasan Kasus"
        description="Asisten kontekstual untuk sintesis kasus, penjelasan bukti, riwayat vendor, alasan penilaian, dan rekomendasi tindakan berikutnya."
        breadcrumbs={[{ label: "Pusat Kendali", href: "/" }, { label: "Asisten Ringkasan Kasus" }]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Setiap jawaban adalah sintesis berbantuan AI berdasar bukti demo. Keputusan akhir memerlukan tinjauan operator berwenang.
      </HelperPanel>

      <div className="grid min-h-[620px] grid-cols-1 gap-6 2xl:grid-cols-[320px_minmax(0,1fr)]">
        <aside className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
          <h2 className="text-lg font-semibold">Konteks Kasus Berisiko Tinggi</h2>
          <p className="mt-1 text-sm text-muted-foreground">Buka sebuah kasus untuk melihat detail lengkapnya.</p>
          <div className="mt-4 space-y-3">
            {cases.slice(0, 5).map((item) => (
              <Link key={item.case_id} href={`/cases/${item.case_id}`} className="block min-w-0 rounded-lg border border-border bg-surface p-4 hover:border-brand-500/60">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between 2xl:flex-col">
                  <EntityChip label={item.case_number ?? caseNumber(item.case_id)} tone="case" />
                  <StatusBadge label={item.priority_label} />
                </div>
                <p className="mt-2 break-words text-sm font-medium">{item.title}</p>
                <p className="mt-1 break-words text-xs text-muted-foreground">{item.vendor_name} · Skor {item.score.final_priority_score}</p>
              </Link>
            ))}
          </div>
        </aside>

        <div className="min-w-0 overflow-hidden rounded-xl border border-border bg-surface-raised shadow-sm">
          <CopilotPanel />
        </div>
      </div>
    </div>
  );
}
