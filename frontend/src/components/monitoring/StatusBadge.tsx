"use client";

import { cn } from "@/lib/utils";

const colorByKeyword: Record<string, string> = {
  // Bahasa Indonesia
  kritis: "border-red-500/40 bg-red-500/10 text-red-300",
  tinggi: "border-orange-500/40 bg-orange-500/10 text-orange-300",
  dieskalasi: "border-red-500/40 bg-red-500/10 text-red-300",
  ditandai: "border-red-500/40 bg-red-500/10 text-red-300",
  menunggu: "border-amber-500/40 bg-amber-500/10 text-amber-300",
  sedang: "border-amber-500/40 bg-amber-500/10 text-amber-300",
  verifikasi: "border-amber-500/40 bg-amber-500/10 text-amber-300",
  baru: "border-brand-500/40 bg-brand-500/10 text-brand-300",
  rendah: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
  sesuai: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
  selesai: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
  // English (kompatibilitas mundur)
  critical: "border-red-500/40 bg-red-500/10 text-red-300",
  high: "border-orange-500/40 bg-orange-500/10 text-orange-300",
  escalated: "border-red-500/40 bg-red-500/10 text-red-300",
  flagged: "border-red-500/40 bg-red-500/10 text-red-300",
  medium: "border-amber-500/40 bg-amber-500/10 text-amber-300",
  review: "border-amber-500/40 bg-amber-500/10 text-amber-300",
  verification: "border-amber-500/40 bg-amber-500/10 text-amber-300",
  open: "border-brand-500/40 bg-brand-500/10 text-brand-300",
  low: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
  compliant: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
  resolved: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
};

export default function StatusBadge({ label, className }: { label: string; className?: string }) {
  const key = Object.keys(colorByKeyword).find((item) => label.toLowerCase().includes(item));
  return (
    <span
      className={cn(
        "inline-flex max-w-full items-center rounded-full border px-2.5 py-1 text-xs font-medium leading-tight whitespace-normal break-words",
        key ? colorByKeyword[key] : "border-border bg-surface-overlay text-muted-foreground",
        className,
      )}
    >
      {label}
    </span>
  );
}
