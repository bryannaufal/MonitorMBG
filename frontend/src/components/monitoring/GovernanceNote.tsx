"use client";

import { ShieldCheck } from "lucide-react";

export default function GovernanceNote({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-brand-500/30 bg-brand-500/10 p-4 text-sm text-brand-800 dark:text-brand-100">
      <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-brand-300" />
      <p className={compact ? "text-xs" : ""}>
        Data dan analisis pada halaman ini merupakan sinyal pra-verifikasi untuk membantu prioritisasi.
        Verifikasi lapangan dan keputusan akhir tetap dilakukan oleh operator berwenang.
      </p>
    </div>
  );
}
