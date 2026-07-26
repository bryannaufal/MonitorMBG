"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  Check,
  ChevronDown,
  CircleHelp,
  Clock,
  FileText,
  History,
  Info as InfoIcon,
  LifeBuoy,
  Lock,
  MapPin,
  MessageSquarePlus,
  Paperclip,
  Printer,
} from "lucide-react";

import { HelperPanel, PageHeader } from "@/components/monitoring/PageHeader";
import { LoadingState } from "@/components/monitoring/PageState";
import StatusBadge from "@/components/monitoring/StatusBadge";
import { api } from "@/lib/api";
import {
  formatDateTime,
  generalLocation,
  publicTimeline,
  relativeTime,
  STAGES,
  statusView,
  submissionChannel,
} from "@/lib/publicTracking";
import { getCase } from "@/lib/reviewStore";
import * as overlay from "@/lib/runtimeOverlay";
import { caseNumber } from "@/lib/utils";
import type { OversightCase } from "@/types/monitoring";

export default function LacakLaporanPage() {
  const params = useParams<{ id: string }>();
  const fallback = getCase(params.id);
  const [item, setItem] = useState<OversightCase | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      let apiCase: OversightCase | null = null;
      try {
        apiCase = await api.get<OversightCase>(`/cases/${params.id}`);
      } catch {
        apiCase = null;
      }
      setItem(overlay.reconcileCase(apiCase ?? fallback, params.id));
      setLoading(false);
    }
    load();
  }, [fallback, params.id]);

  const timeline = useMemo(() => publicTimeline(item?.audit_events ?? []), [item?.audit_events]);

  if (loading) return <LoadingState label="Memuat status laporan…" />;
  if (!item) return <NotFound id={params.id} />;

  const number = item.case_number ?? caseNumber(item.case_id);
  const view = statusView(item.status);
  const latest = timeline[0];

  return (
    // Lebar penuh mengikuti halaman lain; kolomnya baru dipecah di xl agar
    // ruang kosong terpakai tanpa membuat baris teks jadi terlalu panjang.
    <div className="space-y-6">
      <PageHeader
        title={item.title}
        eyebrow={number}
        description="Halaman ini menampilkan perkembangan laporan Anda. Informasi diperbarui setiap kali ada kemajuan penanganan."
        breadcrumbs={[{ label: "Lapor MBG", href: "/lapor" }, { label: "Lacak Laporan" }, { label: number }]}
      />

      {/* 1. Ringkasan status — bagian terpenting, sengaja di paling atas. */}
      <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <p className="text-xs uppercase tracking-wider text-muted-foreground">Status laporan saat ini</p>
            <h2 className="mt-1.5 break-words text-xl font-semibold leading-snug sm:text-2xl">{view.label}</h2>
            <p className="mt-2 max-w-[60ch] break-words text-sm leading-6 text-muted-foreground">{view.meaning}</p>
          </div>
          <StatusBadge label={view.label} className="shrink-0 px-3 py-1.5 text-sm" />
        </div>

        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Info label="Nomor laporan" value={number} />
          <Info label="Jenis isu" value={item.issue_category} />
          <Info label="Dilaporkan" value={formatDateTime(item.created_at)} hint={relativeTime(item.created_at)} />
          <Info label="Diperbarui" value={formatDateTime(item.updated_at)} hint={relativeTime(item.updated_at)} />
        </div>

        <Stepper current={view.stageIndex} state={view.state === "closed" ? "closed" : view.state} />
      </section>

      {/* Dua kolom di layar lebar: alur baca utama di kiri, konteks pendukung
          di kanan. Di bawah xl semuanya kembali menumpuk satu kolom. */}
      <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-3">
      <div className="min-w-0 space-y-6 xl:col-span-2">

      {/* 2. Pembaruan terakhir + langkah berikutnya. */}
      <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <InfoIcon className="h-5 w-5 shrink-0 text-brand-300" /> Pembaruan Terakhir
        </h2>
        {latest ? (
          <div className="mt-4 rounded-lg border border-border bg-surface p-4">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge label={latest.label} />
              <span className="text-xs text-muted-foreground">
                {formatDateTime(latest.timestamp)} · {relativeTime(latest.timestamp)}
              </span>
            </div>
            <p className="mt-2.5 break-words text-sm leading-6">{latest.text}</p>
            <p className="mt-1 text-xs text-muted-foreground">Ditangani oleh {latest.unit}</p>
          </div>
        ) : (
          <p className="mt-4 rounded-lg border border-border bg-surface p-4 text-sm text-muted-foreground">
            Belum ada pembaruan setelah laporan diterima. Kami akan menampilkannya di sini begitu ada kemajuan.
          </p>
        )}

        {view.nextStep ? (
          <div className="mt-3 flex items-start gap-3 rounded-lg border border-border bg-surface p-4">
            <Clock className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            <div className="min-w-0">
              <p className="text-sm font-medium">Langkah berikutnya</p>
              <p className="mt-1 break-words text-sm leading-6 text-muted-foreground">{view.nextStep}</p>
            </div>
          </div>
        ) : null}

        {view.state === "waiting_info" ? (
          <div className="mt-3">
            <HelperPanel>
              Penanganan menunggu keterangan tambahan. Bila Anda punya foto, waktu kejadian, atau detail lain yang
              belum sempat dikirim, tambahkan sekarang agar prosesnya bisa dilanjutkan.
            </HelperPanel>
          </div>
        ) : null}

        {view.state === "completed" && item.resolution_summary ? (
          <div className="mt-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm leading-6 text-emerald-800 dark:text-emerald-200">
            <p className="font-medium">Hasil penanganan</p>
            <p className="mt-1 break-words">{item.resolution_summary}</p>
          </div>
        ) : null}

        {view.state === "closed" ? (
          <div className="mt-3 rounded-lg border border-border bg-surface p-4 text-sm leading-6 text-muted-foreground">
            Laporan ini ditutup. Jika Anda menilai masalahnya masih berlangsung, silakan kirim laporan baru dengan
            informasi terbaru agar dapat ditinjau kembali.
          </div>
        ) : null}
      </section>

      {/* 3. Ringkasan isi laporan. */}
      <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <FileText className="h-5 w-5 shrink-0 text-brand-300" /> Ringkasan Laporan Anda
        </h2>
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Info label="Lokasi umum" value={generalLocation(item)} icon={MapPin} />
          <Info label="Dikirim melalui" value={submissionChannel(item)} />
        </div>
        <p className="mt-4 max-w-[68ch] break-words text-sm leading-6 text-muted-foreground">{item.summary}</p>
        {item.evidence_count > 0 ? (
          <p className="mt-4 flex items-center gap-2 rounded-lg border border-border bg-surface p-3 text-sm text-muted-foreground">
            <Paperclip className="h-4 w-4 shrink-0" />
            {item.evidence_count} lampiran tersimpan dan sudah diterima petugas.
          </p>
        ) : null}
        <p className="mt-3 flex items-start gap-2 text-xs leading-5 text-muted-foreground">
          <Lock className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          Demi privasi dan kelancaran pemeriksaan, sebagian rincian — seperti nama sekolah, identitas pelapor,
          identitas petugas, dan catatan pemeriksaan internal — tidak ditampilkan di halaman ini.
        </p>
      </section>

      </div>

      {/* Kolom kanan: riwayat + aksi. Sticky supaya tetap terlihat saat kolom
          kiri di-scroll pada layar tinggi. */}
      <div className="min-w-0 space-y-6 xl:sticky xl:top-6">

      {/* 4. Riwayat perjalanan — di layar lebar ada ruang, jadi dibuka default. */}
      <details open className="group min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
        <summary className="flex cursor-pointer list-none items-center gap-2 text-lg font-semibold [&::-webkit-details-marker]:hidden">
          <History className="h-5 w-5 shrink-0 text-brand-300" />
          <span>Riwayat Perjalanan Laporan</span>
          <span className="ml-1 truncate text-sm font-normal text-muted-foreground group-open:hidden">
            {timeline.length} pembaruan
          </span>
          <ChevronDown className="ml-auto h-5 w-5 shrink-0 text-muted-foreground transition-transform group-open:rotate-180" />
        </summary>
        {timeline.length ? (
          <ol className="relative mt-4 space-y-4 border-l border-border pl-5">
            {timeline.map((event) => (
              <li key={event.id} className="min-w-0">
                <span className="absolute -left-[6.5px] mt-1.5 h-3 w-3 rounded-full border-2 border-brand-400 bg-surface" />
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge label={event.label} />
                  <span className="text-xs text-muted-foreground">{formatDateTime(event.timestamp)}</span>
                </div>
                <p className="mt-1 break-words text-sm leading-6">{event.text}</p>
                <p className="mt-0.5 break-words text-xs text-muted-foreground">{event.unit}</p>
              </li>
            ))}
          </ol>
        ) : (
          <p className="mt-4 text-sm text-muted-foreground">Belum ada riwayat pembaruan.</p>
        )}
      </details>

      {/* 5. Aksi lanjutan — sengaja dibatasi pada empat hal yang benar-benar berguna. */}
      <section className="min-w-0 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
        <h2 className="text-lg font-semibold">Yang Bisa Anda Lakukan</h2>
        {/* Dua kolom hanya saat menumpuk penuh; di sidebar xl kembali satu kolom. */}
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-1">
          <ActionLink
            href="/lapor"
            icon={MessageSquarePlus}
            title="Tambah informasi"
            detail={`Kirim keterangan atau foto tambahan dengan menyebut nomor ${number}.`}
            primary
          />
          <ActionButton
            icon={Printer}
            title="Unduh bukti laporan"
            detail="Simpan atau cetak halaman ini sebagai tanda terima laporan Anda."
            onClick={() => window.print()}
          />
          <ActionLink
            href="/lapor"
            icon={CircleHelp}
            title="Masalah belum selesai?"
            detail="Laporkan kembali bila keadaan di lapangan belum berubah."
          />
          <ActionLink
            href="mailto:bantuan@monitormbg.id"
            icon={LifeBuoy}
            title="Hubungi bantuan"
            detail="Ada pertanyaan tentang status laporan? Tim bantuan siap membantu."
          />
        </div>
      </section>

      </div>
      </div>

      <p className="text-center text-xs leading-5 text-muted-foreground">
        Simpan nomor laporan <span className="font-mono font-medium text-foreground">{number}</span> untuk mengecek
        status kapan saja. Melaporkan hal yang sama berulang kali tidak mempercepat proses.
      </p>
    </div>
  );
}

/** Kasus tidak ditemukan / nomor salah — tidak pernah membuka laporan lain. */
function NotFound({ id }: { id: string }) {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        title="Laporan tidak ditemukan"
        description="Nomor laporan yang Anda masukkan tidak terdaftar dalam sistem."
        breadcrumbs={[{ label: "Lapor MBG", href: "/lapor" }, { label: "Lacak Laporan" }]}
      />
      <section className="rounded-xl border border-border bg-surface-raised p-4 text-sm leading-6 text-muted-foreground sm:p-5">
        <p className="break-words">
          Kami tidak menemukan laporan dengan nomor <span className="font-mono text-foreground">{id}</span>. Coba
          periksa kembali penulisan nomornya — nomor laporan berbentuk seperti{" "}
          <span className="font-mono text-foreground">MBG-001</span> dan dikirimkan saat laporan Anda diterima.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            href="/lapor"
            className="rounded-md bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-400"
          >
            Kirim laporan baru
          </Link>
          <a
            href="mailto:bantuan@monitormbg.id"
            className="rounded-md border border-border px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-surface"
          >
            Hubungi bantuan
          </a>
        </div>
      </section>
    </div>
  );
}

/**
 * Stepper lima tahap. Horizontal di layar lebar, menumpuk vertikal di ponsel
 * mengikuti pola responsif kartu lain.
 */
function Stepper({ current, state }: { current: number; state: "in_progress" | "completed" | "waiting_info" | "closed" }) {
  return (
    <ol className="mt-6 flex flex-col gap-3 sm:flex-row sm:gap-2">
      {STAGES.map((stage, index) => {
        const done = index < current || (index === current && state === "completed");
        const active = index === current && state !== "completed";
        // Laporan yang ditutup tanpa tuntas: tahap terakhir tidak ditandai hijau.
        const halted = active && (state === "waiting_info" || state === "closed");
        return (
          <li key={stage} className="flex min-w-0 flex-1 items-center gap-3 sm:flex-col sm:items-stretch sm:gap-2">
            <div className="flex items-center gap-2 sm:contents">
              <span
                aria-hidden
                className={
                  "h-1.5 w-1.5 shrink-0 rounded-full sm:h-1.5 sm:w-full " +
                  (done
                    ? "bg-emerald-500"
                    : halted
                      ? "bg-amber-500"
                      : active
                        ? "bg-brand-500"
                        : "bg-surface-overlay")
                }
              />
            </div>
            <div className="flex min-w-0 items-center gap-2">
              {done ? (
                <Check className="h-3.5 w-3.5 shrink-0 text-emerald-500" />
              ) : (
                <span
                  aria-hidden
                  className={
                    "h-3.5 w-3.5 shrink-0 rounded-full border-2 " +
                    (halted ? "border-amber-500" : active ? "border-brand-500" : "border-border")
                  }
                />
              )}
              <span
                className={
                  "break-words text-xs leading-tight " +
                  (done || active ? "font-medium text-foreground" : "text-muted-foreground")
                }
              >
                {stage}
              </span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function Info({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string;
  value: string;
  hint?: string;
  icon?: typeof MapPin;
}) {
  return (
    <div className="min-w-0 rounded-lg bg-surface p-3">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 flex items-start gap-1.5 break-words text-sm font-medium">
        {Icon ? <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" /> : null}
        <span className="min-w-0 break-words">{value}</span>
      </p>
      {hint ? <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

const actionShell =
  "flex min-w-0 items-start gap-3 rounded-lg border border-border bg-surface p-4 text-left transition-colors hover:border-brand-300";

function ActionBody({
  icon: Icon,
  title,
  detail,
  primary,
}: {
  icon: typeof MapPin;
  title: string;
  detail: string;
  primary?: boolean;
}) {
  return (
    <>
      <Icon className={"mt-0.5 h-4 w-4 shrink-0 " + (primary ? "text-brand-300" : "text-muted-foreground")} />
      <span className="min-w-0">
        <span className="block break-words text-sm font-medium">{title}</span>
        <span className="mt-1 block break-words text-xs leading-5 text-muted-foreground">{detail}</span>
      </span>
    </>
  );
}

function ActionLink(props: { href: string; icon: typeof MapPin; title: string; detail: string; primary?: boolean }) {
  const { href, ...body } = props;
  return (
    <Link href={href} className={actionShell}>
      <ActionBody {...body} />
    </Link>
  );
}

function ActionButton(props: {
  onClick: () => void;
  icon: typeof MapPin;
  title: string;
  detail: string;
  primary?: boolean;
}) {
  const { onClick, ...body } = props;
  return (
    <button type="button" onClick={onClick} className={actionShell}>
      <ActionBody {...body} />
    </button>
  );
}
