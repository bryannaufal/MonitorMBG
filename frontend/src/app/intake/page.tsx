"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ClipboardList, FileText, Megaphone, MessageSquareWarning } from "lucide-react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { getWithFallback } from "@/lib/api";
import { asList, fallbackCases, fallbackSignals } from "@/lib/demoFallback";
import { applySignals, overlayCases } from "@/lib/runtimeOverlay";
import { caseNumber } from "@/lib/utils";
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

export default function IntakePage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [caseStatus, setCaseStatus] = useState<Record<string, string>>({});
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);

  const [queue, setQueue] = useState<Queue>("action");
  const [fSource, setFSource] = useState(ANY);
  const [fUrgency, setFUrgency] = useState(ANY);
  const [fRegion, setFRegion] = useState(ANY);

  useEffect(() => {
    async function load() {
      const [sigRes, caseRes] = await Promise.all([
        getWithFallback<ListResponse<Signal>>("/signals", asList(fallbackSignals)),
        getWithFallback<ListResponse<OversightCase>>("/cases", asList(fallbackCases)),
      ]);
      // Overlay runtime menang: tautan/kasus hasil fusion pada sesi ini tetap
      // tampil walau API sudah restart dan mengembalikan data seed.
      setSignals(applySignals(sigRes.data.items));
      const statusMap: Record<string, string> = {};
      for (const c of caseRes.data.items) statusMap[c.case_id] = c.status;
      for (const c of overlayCases()) statusMap[c.case_id] = c.status;
      setCaseStatus(statusMap);
      setSource(sigRes.source === "api" && caseRes.source === "api" ? "api" : "fallback");
      setError(sigRes.error ?? caseRes.error);
      setLoading(false);
    }
    load();
  }, []);

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
    return signals
      .filter((s) => (queue === "all" ? true : classify(s) === queue))
      .filter((s) => (fSource === ANY || s.source === fSource))
      .filter((s) => (fUrgency === ANY || s.urgency === fUrgency))
      .filter((s) => (fRegion === ANY || s.region === fRegion))
      .sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signals, caseStatus, queue, fSource, fUrgency, fRegion]);

  if (loading) return <LoadingState />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Kotak Masuk Sinyal"
        description="Antrean kerja operator: sinyal MBG masuk di sini, ditinjau, dibentuk menjadi kasus, lalu tetap dapat dilacak untuk audit dan investigasi."
        breadcrumbs={[{ label: "Pusat Kendali", href: "/" }, { label: "Kotak Masuk Sinyal" }]}
        source={source}
        error={error}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Sinyal yang sudah ditangani tidak dihapus dari antrean. Gunakan tab status untuk memisahkan yang{" "}
        <span className="font-medium">perlu tindakan</span> dari yang sudah <span className="font-medium">terhubung ke kasus</span> atau{" "}
        <span className="font-medium">selesai/arsip</span>.
      </HelperPanel>

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

      <section className="grid grid-cols-1 gap-3 rounded-xl border border-border bg-surface-raised p-4 sm:grid-cols-3">
        <FilterSelect label="Sumber" value={fSource} options={options.sources} onChange={setFSource} />
        <FilterSelect label="Tingkat Urgensi" value={fUrgency} options={options.urgencies} onChange={setFUrgency} />
        <FilterSelect label="Wilayah" value={fRegion} options={options.regions} onChange={setFRegion} />
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
                          <p className="mt-1 text-xs text-muted-foreground">
                            {signal.source} · {new Date(signal.created_at).toLocaleString("id-ID")}
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
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
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
          <option key={opt} value={opt}>{opt}</option>
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
