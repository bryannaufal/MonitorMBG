"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Search } from "lucide-react";

import { HelperPanel, PageHeader } from "@/components/monitoring/PageHeader";

/** `MBG-001` / `001` / `case-001` -> `case-001` (id kasus internal). */
function toCaseId(input: string): string | null {
  const digits = input.replace(/\D/g, "");
  return digits ? `case-${digits.padStart(3, "0")}` : null;
}

export default function LacakLookupPage() {
  const router = useRouter();
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const caseId = toCaseId(value);
    if (!caseId) {
      setError("Masukkan nomor laporan seperti MBG-001.");
      return;
    }
    router.push(`/lacak/${caseId}`);
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader
        title="Lacak Laporan"
        description="Masukkan nomor laporan Anda untuk melihat sejauh mana penanganannya sudah berjalan."
        breadcrumbs={[{ label: "Lapor MBG", href: "/lapor" }, { label: "Lacak Laporan" }]}
      />
      <HelperPanel>
        Nomor laporan Anda terlihat seperti <span className="font-mono font-medium">MBG-001</span> dan diberikan saat
        laporan diterima. Tidak perlu login.
      </HelperPanel>

      <form onSubmit={submit} className="space-y-3 rounded-xl border border-border bg-surface-raised p-4 sm:p-5">
        <label className="block text-sm">
          <span className="font-medium">Nomor laporan</span>
          <input
            value={value}
            onChange={(e) => {
              setValue(e.target.value);
              setError(null);
            }}
            placeholder="MBG-001"
            className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm"
          />
        </label>
        {error ? <p className="text-xs text-amber-700 dark:text-amber-300">{error}</p> : null}
        <button
          type="submit"
          className="inline-flex items-center gap-2 rounded-md bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-400"
        >
          <Search className="h-4 w-4" /> Lihat status laporan
        </button>
      </form>
    </div>
  );
}
