"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowDownWideNarrow, Filter, Search } from "lucide-react";

import { EntityChip, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { asList, fallbackCases } from "@/lib/demoFallback";
import { overlayCases } from "@/lib/runtimeOverlay";
import { fmtGizi, fmtScore, normalizeCase } from "@/lib/scoreDisplay";
import type { ListResponse, OversightCase } from "@/types/monitoring";

// Urutan daftar kasus. Default mengikuti backend (demo_data.oversight_cases):
// skor prioritas tertinggi di atas.
const SORTS = {
  "Skor tertinggi": (a: OversightCase, b: OversightCase) =>
    b.score.final_priority_score - a.score.final_priority_score,
  "Terbaru diperbarui": (a: OversightCase, b: OversightCase) =>
    Date.parse(b.updated_at) - Date.parse(a.updated_at),
  "Bukti terbanyak": (a: OversightCase, b: OversightCase) =>
    b.evidence_count - a.evidence_count,
} satisfies Record<string, (a: OversightCase, b: OversightCase) => number>;

type SortKey = keyof typeof SORTS;

export default function CasesPage() {
  const [cases, setCases] = useState<OversightCase[]>([]);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [priority, setPriority] = useState("Semua");
  const [status, setStatus] = useState("Semua");
  const [region, setRegion] = useState("Semua");
  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState<SortKey>("Skor tertinggi");

  useEffect(() => {
    async function load() {
      const result = await getWithFallback<ListResponse<OversightCase>>("/cases", asList(fallbackCases));
      const merged = [...result.data.items.map(normalizeCase)];
      for (const c of overlayCases()) {
        const normalized = normalizeCase(c);
        const idx = merged.findIndex((item) => item.case_id === normalized.case_id);
        if (idx >= 0) merged[idx] = normalizeCase({ ...merged[idx], ...normalized, score: normalized.score });
        else merged.push(normalized);
      }
      // Urutan tampil ditentukan `filtered` (lihat SORTS), jadi urutan array di
      // sini tidak penting — termasuk kasus overlay yang di-push ke akhir.
      setCases(merged);
      setSource(result.source);
      setError(result.error);
      setLoading(false);
    }
    load();
  }, []);

  useEffect(() => {
    const selectedRegion = new URLSearchParams(window.location.search).get("region");
    if (selectedRegion) setRegion(selectedRegion);
  }, []);

  const filtered = useMemo(() => {
    const rows = cases.filter((item) => {
      const haystack = `${item.title} ${item.vendor_name} ${item.school} ${item.case_id} ${item.issue_category}`.toLowerCase();
      return (
        (priority === "Semua" || item.priority_label === priority) &&
        (status === "Semua" || item.status === status) &&
        (region === "Semua" || item.region === region) &&
        (!query || haystack.includes(query.toLowerCase()))
      );
    });
    // Salin sebelum sort: filter() memang sudah menghasilkan array baru, tapi
    // sort di sini yang menentukan urutan tampil — termasuk kasus overlay yang
    // ditambahkan di akhir saat load.
    return rows.sort(SORTS[sortBy]);
  }, [cases, priority, query, region, status, sortBy]);

  if (loading) return <LoadingState />;

  const regions = Array.from(new Set(cases.map((item) => item.region)));
  const statuses = Array.from(new Set(cases.map((item) => item.status)));
  const highRisk = cases.filter((item) => ["Kritis", "Tinggi"].includes(item.priority_label)).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Kasus"
        description="Kasus pengawasan berprioritas yang dibentuk dari sinyal publik, laporan, bukti harian vendor, dan penilaian risiko."
        breadcrumbs={[{ label: "Pusat Kendali", href: "/" }, { label: "Kasus" }]}
        source={source}
        error={error}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile label="Kasus Aktif" value={String(cases.filter((item) => !["Closed", "Merged / Invalid"].includes(item.status)).length)} detail="Dibentuk dari sinyal intake terhubung" />
        <MetricTile label="Kritis/Tinggi" value={String(highRisk)} detail="Perlu ditinjau segera" />
        <MetricTile label="Butir Bukti" value={String(cases.reduce((sum, item) => sum + item.evidence_count, 0))} detail="Terlampir pada kasus" />
        <MetricTile label="Workstream terbuka" value={String(cases.reduce((sum, item) => sum + (item.tickets ?? (item.ticket ? [item.ticket] : [])).filter((ticket) => ticket.status !== "Selesai").length, 0))} detail="Tiket anak opsional" />
      </div>

      <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
          <div className="relative min-w-0 flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Cari kasus, vendor, sekolah, isu..."
              className="h-9 w-full rounded-md border border-border bg-surface pl-9 pr-3 text-sm outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:flex xl:shrink-0">
            <FilterSelect label="Prioritas" value={priority} options={["Semua", "Kritis", "Tinggi", "Sedang", "Rendah"]} onChange={setPriority} />
            <FilterSelect label="Status" value={status} options={["Semua", ...statuses]} onChange={setStatus} />
            <FilterSelect label="Wilayah" value={region} options={["Semua", ...regions]} onChange={setRegion} />
            <FilterSelect label="Urutkan" value={sortBy} options={Object.keys(SORTS)} onChange={(v) => setSortBy(v as SortKey)} />
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {filtered.map((item) => (
          <article key={item.case_id} className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap gap-2">
                  <EntityChip label={item.case_number} href={`/cases/${item.case_id}`} tone="case" />
                  <EntityChip label={item.vendor_name} href={`/vendors/${item.vendor_id}`} tone="vendor" />
                  {(item.tickets?.length ?? (item.ticket_id ? 1 : 0)) ? <EntityChip label={`${item.tickets?.length ?? 1} workstream`} tone="ticket" /> : <StatusBadge label="Tangani langsung" />}
                </div>
                <h2 className="mt-3 break-words text-lg font-semibold">{item.title}</h2>
                <p className="mt-1 break-words text-sm text-muted-foreground">
                  {item.school} · {item.district}, {item.region} · {item.issue_category}
                </p>
              </div>
              <div className="flex shrink-0 flex-row flex-wrap gap-2 sm:flex-col sm:items-end">
                <StatusBadge label={item.priority_label} />
                <StatusBadge label={item.status} />
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-7">
              <Mini label="DAMPAK" value={fmtScore(item.score.severity_score)} />
              <Mini label="KEYAKINAN" value={fmtScore(item.score.confidence_score)} />
              <Mini label="DAPAT DITINDAK" value={fmtScore(item.score.actionability_score)} />
              <Mini label="GIZI" value={fmtGizi(item.score.nutrition_score)} />
              <Mini label="Skor Akhir" value={fmtScore(item.score.final_priority_score)} />
              <Mini label="Sinyal" value={String(item.signals_count)} />
              <Mini label="SLA" value={item.sla_status} />
            </div>

            <p className="mt-4 break-words text-sm leading-6 text-muted-foreground">{item.recommended_action}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link href={`/cases/${item.case_id}`} className="inline-flex justify-center rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-400">
                Buka Kasus
              </Link>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  // "Urutkan" mengubah urutan, bukan menyaring — ikonnya dibedakan.
  const Icon = label === "Urutkan" ? ArrowDownWideNarrow : Filter;
  return (
    <label className="flex min-w-0 items-center gap-2 text-sm text-muted-foreground">
      <span className="hidden items-center gap-1 lg:inline-flex">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-9 w-full min-w-0 rounded-md border border-border bg-surface px-3 text-sm text-foreground outline-none focus:ring-1 focus:ring-brand-500"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg bg-surface p-3">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 break-words text-sm font-semibold">{value}</p>
    </div>
  );
}
