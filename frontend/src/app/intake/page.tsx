"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ClipboardList, FileText, Loader2, Megaphone, MessageSquareWarning } from "lucide-react";

import { EntityChip, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { asList, fallbackCases, fallbackSignals } from "@/lib/demoFallback";
import { readIntakeCache, writeIntakeCache } from "@/lib/intakeCache";
import { applySignals, overlayCases } from "@/lib/runtimeOverlay";
import {
  getScrapeStatus,
  isScrapeBusy,
  readStoredScrapeStatus,
  resumeScrapePolling,
  startScrape,
  subscribeScrape,
  type ScrapeJobStatus,
} from "@/lib/scrapeSession";
import { caseNumber, signalPriorityScore } from "@/lib/utils";
import type { ListResponse, OversightCase, Signal } from "@/types/monitoring";

const ANY = "Semua";

// Kategori work queue operasional. Signal tidak dihapus; hanya dikelompokkan.
type Queue = "action" | "linked" | "done" | "all";
const QUEUES: { id: Queue; label: string }[] = [
  { id: "action", label: "Perlu Tindakan" },
  { id: "linked", label: "Terhubung ke Kasus" },
  { id: "done", label: "Selesai / Arsip" },
  { id: "all", label: "Semua Signal" },
];

const DONE_STATUSES = new Set(["Selesai", "Selesai / Arsip", "Ditutup"]);

type SortBy = "recent" | "priority";
const SORT_OPTIONS: { id: SortBy; label: string }[] = [
  { id: "recent", label: "Terbaru" },
  { id: "priority", label: "Prioritas tertinggi" },
];

export default function IntakePage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [caseStatus, setCaseStatus] = useState<Record<string, string>>({});
  const [casePriority, setCasePriority] = useState<Record<string, number>>({});
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [scrapeStatus, setScrapeStatus] = useState<ScrapeJobStatus>(() => getScrapeStatus());
  const [scrapeError, setScrapeError] = useState<string | null>(null);

  const applyListData = useCallback(
    (
      sigItems: Signal[],
      caseItems: OversightCase[],
      nextSource: "api" | "fallback",
      nextError?: string,
    ) => {
      setSignals(applySignals(sigItems));
      const statusMap: Record<string, string> = {};
      const priorityMap: Record<string, number> = {};
      for (const c of caseItems) {
        statusMap[c.case_id] = c.status;
        priorityMap[c.case_id] = c.score?.final_priority_score ?? 0;
      }
      for (const c of overlayCases()) {
        statusMap[c.case_id] = c.status;
        priorityMap[c.case_id] = c.score?.final_priority_score ?? priorityMap[c.case_id] ?? 0;
      }
      setCaseStatus(statusMap);
      setCasePriority(priorityMap);
      setSource(nextSource);
      setError(nextError);
      writeIntakeCache({
        signals: applySignals(sigItems),
        caseStatus: statusMap,
        casePriority: priorityMap,
        source: nextSource,
        error: nextError,
      });
    },
    [],
  );

  const loadInbox = useCallback(
    async (opts?: { preferCacheOnFallback?: boolean }) => {
      const cached = readIntakeCache();
      const [sigRes, caseRes] = await Promise.all([
        getWithFallback<ListResponse<Signal>>("/signals", asList(fallbackSignals)),
        getWithFallback<ListResponse<OversightCase>>("/cases", asList(fallbackCases)),
      ]);

      const apiOk = sigRes.source === "api" && caseRes.source === "api";
      if (!apiOk && opts?.preferCacheOnFallback && cached) {
        setSignals(cached.signals);
        setCaseStatus(cached.caseStatus);
        setCasePriority(cached.casePriority);
        setSource(cached.source);
        setError(sigRes.error ?? caseRes.error ?? cached.error);
        return;
      }

      const mergedCases = [...caseRes.data.items];
      for (const c of overlayCases()) {
        if (!mergedCases.some((item) => item.case_id === c.case_id)) mergedCases.push(c);
      }
      applyListData(
        sigRes.data.items,
        mergedCases,
        apiOk ? "api" : "fallback",
        sigRes.error ?? caseRes.error,
      );
    },
    [applyListData],
  );

  useEffect(() => {
    const cached = readIntakeCache();
    const storedScrape = readStoredScrapeStatus();
    if (cached) {
      setSignals(cached.signals);
      setCaseStatus(cached.caseStatus);
      setCasePriority(cached.casePriority);
      setSource(cached.source);
      setError(cached.error);
      setLoading(false);
    }
    if (storedScrape) setScrapeStatus(storedScrape);

    resumeScrapePolling();
    const unsub = subscribeScrape(setScrapeStatus);

    void loadInbox({ preferCacheOnFallback: !!cached }).finally(() => setLoading(false));

    return unsub;
  }, [loadInbox]);

  useEffect(() => {
    if (scrapeStatus.phase === "done") {
      setScrapeError(null);
      void loadInbox();
      return;
    }
    if (scrapeStatus.phase === "error") {
      setScrapeError(scrapeStatus.error ?? "Scrape gagal.");
    }
  }, [scrapeStatus.phase, scrapeStatus.job_id, scrapeStatus.error, loadInbox]);

  async function runScrape() {
    setScrapeError(null);
    try {
      await startScrape();
    } catch {
      setScrapeError("Scrape gagal — pastikan backend berjalan.");
    }
  }

  const scraping = isScrapeBusy(scrapeStatus);
  const scrapeMsg =
    scrapeStatus.phase === "done" && scrapeStatus.result?.message
      ? scrapeStatus.result.message
      : null;

  const [queue, setQueue] = useState<Queue>("action");
  const [fSource, setFSource] = useState(ANY);
  const [fUrgency, setFUrgency] = useState(ANY);
  const [fRegion, setFRegion] = useState(ANY);
  const [sortBy, setSortBy] = useState<SortBy>("recent");

  function intakeBadge(origin?: string) {
    if (!origin) return null;
    if (origin === "scraper_live") return <StatusBadge label="RSS Live" />;
    if (origin === "scraper_twitter") return <StatusBadge label="X Live" />;
    if (origin === "scraper_fixture") return <StatusBadge label="Scraped" />;
    if (origin === "public_form") return <StatusBadge label="Formulir" />;
    return null;
  }

  function classify(s: Signal): Queue {
    if (!s.case_id) return "action";
    const status = caseStatus[s.case_id];
    return status && DONE_STATUSES.has(status) ? "done" : "linked";
  }

  const counts = useMemo(() => {
    const c = { action: 0, linked: 0, done: 0, all: signals.length };
    for (const s of signals) c[classify(s)] += 1;
    return c;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signals, caseStatus]);

  const options = useMemo(() => {
    const uniq = (get: (s: Signal) => string) => [ANY, ...Array.from(new Set(signals.map(get))).filter(Boolean).sort()];
    return { sources: uniq((s) => s.source), urgencies: uniq((s) => s.urgency), regions: uniq((s) => s.region) };
  }, [signals]);

  const visible = useMemo(() => {
    const filtered = signals
      .filter((s) => (queue === "all" ? true : classify(s) === queue))
      .filter((s) => (fSource === ANY || s.source === fSource))
      .filter((s) => (fUrgency === ANY || s.urgency === fUrgency))
      .filter((s) => (fRegion === ANY || s.region === fRegion));

    return filtered.sort((a, b) => {
      if (sortBy === "priority") {
        const diff = signalPriorityScore(b, casePriority) - signalPriorityScore(a, casePriority);
        if (diff !== 0) return diff;
      }
      return Date.parse(b.created_at) - Date.parse(a.created_at);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signals, caseStatus, casePriority, queue, fSource, fUrgency, fRegion, sortBy]);

  if (loading && signals.length === 0) return <LoadingState label="Memuat Kotak Masuk Sinyal..." />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Kotak Masuk Sinyal"
        description="Antrean kerja operator: sinyal MBG masuk di sini, ditinjau, dibentuk menjadi kasus, lalu tetap dapat dilacak untuk audit dan investigasi."
        breadcrumbs={[{ label: "Pusat Kendali", href: "/" }, { label: "Kotak Masuk Sinyal" }]}
        source={source}
        error={error}
        action={
          <button
            type="button"
            onClick={runScrape}
            disabled={scraping}
            className="rounded-md bg-brand-500 px-3 py-2 text-xs font-medium text-white hover:bg-brand-400 disabled:opacity-50"
          >
            {scraping ? "Scraping…" : "Scrape Sosmed"}
          </button>
        }
      />
      <ScrapeProgress status={scrapeStatus} />
      {scrapeMsg ? <p className="text-sm text-emerald-400">{scrapeMsg}</p> : null}
      {scrapeError ? <p className="text-sm text-red-400">{scrapeError}</p> : null}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricTile label="Total Signal" value={String(counts.all)} />
        <MetricTile label="Perlu Tindakan" value={String(counts.action)} />
        <MetricTile label="Terhubung ke Kasus" value={String(counts.linked)} />
        <MetricTile label="Selesai / Arsip" value={String(counts.done)} />
      </div>

      {/* Tab status work queue */}
      <div className="overflow-x-auto rounded-xl border border-border bg-surface-raised p-2">
        <div className="flex min-w-max gap-2">
          {QUEUES.map((q) => (
            <button
              key={q.id}
              onClick={() => setQueue(q.id)}
              className={`shrink-0 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                queue === q.id ? "bg-brand-500 text-white" : "text-muted-foreground hover:bg-surface hover:text-foreground"
              }`}
            >
              {q.label} <span className="ml-1 opacity-70">({counts[q.id]})</span>
            </button>
          ))}
        </div>
      </div>

      <section className="grid grid-cols-1 gap-3 rounded-xl border border-border bg-surface-raised p-4 sm:grid-cols-2 lg:grid-cols-4">
        <FilterSelect label="Sumber" value={fSource} options={options.sources} onChange={setFSource} />
        <FilterSelect label="Tingkat Urgensi" value={fUrgency} options={options.urgencies} onChange={setFUrgency} />
        <FilterSelect label="Wilayah" value={fRegion} options={options.regions} onChange={setFRegion} />
        <FilterSelect
          label="Urutkan"
          value={sortBy}
          options={SORT_OPTIONS.map((o) => o.id)}
          optionLabels={Object.fromEntries(SORT_OPTIONS.map((o) => [o.id, o.label]))}
          onChange={(v) => setSortBy(v as SortBy)}
        />
      </section>

      <section className="min-w-0 overflow-hidden rounded-xl border border-border bg-surface-raised">
        <div className="overflow-x-auto">
          <table className="min-w-[920px] w-full text-left text-sm">
            <thead className="border-b border-border bg-surface-overlay text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-4 py-3">Sinyal</th>
                <th className="px-4 py-3">Kategori Isu</th>
                <th className="px-4 py-3">Vendor / Sekolah / Wilayah</th>
                <th className="px-4 py-3">Urgensi</th>
                <th className="px-4 py-3">Hubungan Kasus</th>
                <th className="px-4 py-3">Tindakan</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((signal) => {
                const q = classify(signal);
                return (
                  <tr key={signal.id} className="border-b border-border hover:bg-surface">
                    <td className="px-4 py-4">
                      <div className="flex items-start gap-3">
                        <SourceIcon source={signal.source} />
                        <div>
                          <p className="line-clamp-2 break-words font-medium">{signal.summary}</p>
                          <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                            <span>{signal.source} · {new Date(signal.created_at).toLocaleString("id-ID")}</span>
                            {intakeBadge(signal.intake_origin)}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <StatusBadge label={signal.issue_category} />
                    </td>
                    <td className="px-4 py-4">
                      {signal.vendor_id ? (
                        <EntityChip label={signal.vendor_name} href={`/vendors/${signal.vendor_id}`} tone="vendor" />
                      ) : (
                        <StatusBadge label="Belum teridentifikasi" />
                      )}
                      <p className="mt-2 break-words text-xs text-muted-foreground">{signal.school} · {signal.region}</p>
                    </td>
                    <td className="px-4 py-4">
                      <StatusBadge label={signal.urgency} />
                      <p className="mt-1 text-xs text-muted-foreground">Keyakinan {Math.round(signal.source_confidence * 100)}%</p>
                    </td>
                    <td className="px-4 py-4">
                      {signal.case_id ? (
                        <EntityChip label={caseNumber(signal.case_id)} href={`/cases/${signal.case_id}`} tone="case" />
                      ) : (
                        <StatusBadge label="Belum dibentuk kasus" />
                      )}
                      <div className="mt-2"><StatusBadge label={signal.status} /></div>
                    </td>
                    <td className="px-4 py-4">
                      <CtaCell signalId={signal.id} caseId={signal.case_id} queue={q} />
                    </td>
                  </tr>
                );
              })}
              {visible.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-10 text-center text-sm text-muted-foreground">
                    Tidak ada sinyal pada tab/filter ini.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

// CTA mengikuti status: terhubung → Buka Kasus; selesai → Lihat Kasus;
// belum terhubung → Tinjau & Bentuk Kasus. Tidak pernah menawarkan pembentukan
// kasus baru untuk sinyal yang sudah terhubung.
function ScrapeProgress({ status }: { status: ScrapeJobStatus }) {
  const busy = isScrapeBusy(status);
  const showError = status.phase === "error";
  if (!busy && !showError) return null;

  const total = status.total ?? 0;
  const current = status.current ?? 0;
  const pct =
    status.phase === "scoring" && total > 0
      ? Math.round((current / total) * 100)
      : status.phase === "fetching"
        ? null
        : status.phase === "done"
          ? 100
          : 0;

  return (
    <div className="rounded-xl border border-brand-500/30 bg-brand-500/5 p-4">
      <div className="flex items-center gap-2 text-sm font-medium text-foreground">
        {busy ? <Loader2 className="h-4 w-4 shrink-0 animate-spin text-brand-300" /> : null}
        <span>{status.label ?? "Memproses scrape..."}</span>
        {status.phase === "scoring" && total > 0 ? (
          <span className="text-muted-foreground">
            ({current}/{total})
          </span>
        ) : null}
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface-overlay">
        {pct === null ? (
          <div className="h-full w-1/3 animate-pulse rounded-full bg-brand-400" />
        ) : (
          <div
            className="h-full rounded-full bg-brand-400 transition-all duration-500"
            style={{ width: `${Math.max(pct, busy ? 8 : 0)}%` }}
          />
        )}
      </div>
      {busy ? (
        <p className="mt-2 text-xs text-muted-foreground">
          Scrape berjalan di server — Anda bisa pindah tab; progress akan lanjut saat kembali ke halaman ini.
        </p>
      ) : null}
    </div>
  );
}

function CtaCell({ signalId, caseId, queue }: { signalId: number; caseId: string | null; queue: Queue }) {
  if (caseId && queue === "linked") {
    return (
      <Link href={`/cases/${caseId}`} className="inline-block rounded-md bg-brand-500 px-3 py-2 text-xs font-medium text-white hover:bg-brand-400">
        Buka Kasus
      </Link>
    );
  }
  if (caseId && queue === "done") {
    return (
      <Link href={`/cases/${caseId}`} className="inline-block rounded-md border border-border px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-surface hover:text-foreground">
        Lihat Kasus
      </Link>
    );
  }
  return (
    <Link href={`/signals/${signalId}/review`} className="inline-block rounded-md border border-border px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-surface hover:text-foreground">
      Tinjau &amp; Bentuk Kasus
    </Link>
  );
}

function FilterSelect({
  label,
  value,
  options,
  optionLabels,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  optionLabels?: Record<string, string>;
  onChange: (value: string) => void;
}) {
  return (
    <label className="min-w-0 text-xs">
      <span className="mb-1 block uppercase text-muted-foreground">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>{optionLabels?.[opt] ?? opt}</option>
        ))}
      </select>
    </label>
  );
}

function SourceIcon({ source }: { source: string }) {
  const s = source.toLowerCase();
  const Icon = s.includes("pengawas") || s.includes("pengadaan")
    ? FileText
    : s.includes("harian")
      ? ClipboardList
      : s.includes("sosial") || s.includes("publik") || s.includes("komunitas")
        ? Megaphone
        : MessageSquareWarning;
  return <Icon className="mt-0.5 h-4 w-4 shrink-0 text-brand-300" />;
}
