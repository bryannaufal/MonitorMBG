"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ImagePlus, Send, X } from "lucide-react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { HelperPanel, PageHeader } from "@/components/monitoring/PageHeader";
import { api, ApiError } from "@/lib/api";

const ISSUES = [
  "dugaan keamanan pangan",
  "porsi protein kurang",
  "anomali biaya",
  "kekhawatiran higiene",
  "keterlambatan distribusi",
  "belum diklasifikasi",
];

const MAX_PHOTO_BYTES = 5 * 1024 * 1024;
const ACCEPTED_PHOTO_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];

export default function LaporPage() {
  const [description, setDescription] = useState("");
  const [issueCategory, setIssueCategory] = useState(ISSUES[0]);
  const [region, setRegion] = useState("");
  const [district, setDistrict] = useState("");
  const [school, setSchool] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);

  useEffect(() => {
    if (!photo) {
      setPhotoPreview(null);
      return;
    }
    const url = URL.createObjectURL(photo);
    setPhotoPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [photo]);

  function onPhotoChange(file: File | null) {
    setPhotoError(null);
    if (!file) {
      setPhoto(null);
      return;
    }
    if (!ACCEPTED_PHOTO_TYPES.includes(file.type)) {
      setPhoto(null);
      setPhotoError("Format tidak didukung. Gunakan JPG, PNG, WEBP, atau GIF.");
      return;
    }
    if (file.size > MAX_PHOTO_BYTES) {
      setPhoto(null);
      setPhotoError("Ukuran foto maksimal 5 MB.");
      return;
    }
    setPhoto(file);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setResult(null);
    try {
      const body = new FormData();
      body.append("description", description);
      body.append("issue_category", issueCategory);
      if (region.trim()) body.append("region", region.trim());
      if (district.trim()) body.append("district", district.trim());
      if (school.trim()) body.append("school", school.trim());
      if (photo) body.append("photo", photo);

      const res = await api.postForm<{
        duplicate?: boolean;
        message: string;
      }>("/intake/form", body);

      setResult({
        ok: !res.duplicate,
        message: res.message,
      });
      if (!res.duplicate) {
        setDescription("");
        setPhoto(null);
        setPhotoError(null);
      }
    } catch (err) {
      const msg = err instanceof ApiError ? err.message.replace(/^API error: /, "") : "Gagal mengirim laporan. Pastikan backend berjalan di port 8000.";
      setResult({ ok: false, message: msg });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader
        title="Lapor MBG"
        description="Formulir publik untuk melaporkan dugaan isu Makan Bergizi Gratis. Tidak perlu login — laporan masuk sebagai sinyal pra-verifikasi."
        breadcrumbs={[{ label: "Beranda", href: "/" }, { label: "Lapor MBG" }]}
      />
      <GovernanceNote compact />
      <HelperPanel>
        Laporan masuk ke <span className="font-medium">Kotak Masuk Sinyal</span> untuk ditinjau operator — bukan langsung ke tiket atau kasus.
        Foto bukti opsional (JPG/PNG/WEBP/GIF, maks. 5 MB).
      </HelperPanel>

      <form onSubmit={submit} className="space-y-4 rounded-xl border border-border bg-surface-raised p-5">
        <label className="block text-sm">
          <span className="font-medium">Jenis isu</span>
          <select value={issueCategory} onChange={(e) => setIssueCategory(e.target.value)} className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm">
            {ISSUES.map((i) => (
              <option key={i} value={i}>{i}</option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          <span className="font-medium">Cerita / detail laporan *</span>
          <textarea required minLength={10} value={description} onChange={(e) => setDescription(e.target.value)} rows={5} className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm" placeholder="Jelaskan kejadian, lokasi, dan waktu jika ada..." />
        </label>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <label className="block text-sm">
            <span className="font-medium">Provinsi</span>
            <input value={region} onChange={(e) => setRegion(e.target.value)} className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm" />
          </label>
          <label className="block text-sm">
            <span className="font-medium">Kabupaten/Kota</span>
            <input value={district} onChange={(e) => setDistrict(e.target.value)} className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm" />
          </label>
          <label className="block text-sm">
            <span className="font-medium">Sekolah</span>
            <input value={school} onChange={(e) => setSchool(e.target.value)} className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm" />
          </label>
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-medium">Foto bukti (opsional)</p>
              <p className="mt-1 text-xs text-muted-foreground">JPG, PNG, WEBP, atau GIF — maks. 5 MB. Kosongkan jika tidak ada foto.</p>
            </div>
            <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-border px-3 py-2 text-xs font-medium hover:bg-surface-raised">
              <ImagePlus className="h-4 w-4" />
              Pilih foto
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                className="sr-only"
                onChange={(e) => onPhotoChange(e.target.files?.[0] ?? null)}
              />
            </label>
          </div>
          {photoError ? <p className="mt-2 text-xs text-amber-700 dark:text-amber-300">{photoError}</p> : null}
          {photoPreview ? (
            <div className="mt-4 max-w-sm">
              <div className="relative aspect-video overflow-hidden rounded-md border border-border bg-surface-overlay">
                <Image src={photoPreview} alt="Pratinjau foto laporan" fill unoptimized className="object-cover" sizes="400px" />
              </div>
              <div className="mt-2 flex items-center justify-between gap-2 text-xs text-muted-foreground">
                <span className="truncate">{photo?.name}</span>
                <button
                  type="button"
                  onClick={() => onPhotoChange(null)}
                  className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 hover:bg-surface-raised"
                >
                  <X className="h-3 w-3" /> Hapus
                </button>
              </div>
            </div>
          ) : null}
        </div>

        <button type="submit" disabled={submitting} className="inline-flex items-center gap-2 rounded-md bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-400 disabled:opacity-50">
          <Send className="h-4 w-4" /> {submitting ? "Mengirim…" : "Kirim Laporan"}
        </button>
      </form>

      {result ? (
        <div className={`rounded-lg border p-4 text-sm ${result.ok ? "border-emerald-500/30 bg-emerald-500/10" : "border-amber-500/30 bg-amber-500/10"}`}>
          <p>{result.message}</p>
          {result.ok ? (
            <p className="mt-2 text-xs text-muted-foreground">
              Operator meninjau di{" "}
              <Link href="/intake" className="text-brand-600 underline dark:text-brand-300">Kotak Masuk Sinyal</Link>
              {" "}sebelum kasus atau tiket dibuat.
            </p>
          ) : null}
        </div>
      ) : null}

      <p className="text-center text-xs text-muted-foreground">
        Operator? <Link href="/intake" className="text-brand-600 underline dark:text-brand-300">Kotak Masuk Sinyal</Link>
      </p>
    </div>
  );
}
