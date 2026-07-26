/** Bar skor GIZI — di bawah grid 2×2; tidak masuk rumus skor prioritas. */
export default function GiziBar({
  value,
  hint = "Belum dinilai (tanpa foto).",
  note,
}: {
  value: number | null | undefined;
  hint?: string;
  note?: string;
}) {
  if (value == null) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-surface p-4">
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm font-medium leading-snug">Gizi (estimasi porsi)</p>
          <p className="shrink-0 text-sm font-semibold text-muted-foreground">—</p>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface-overlay" />
        <p className="mt-2 text-xs text-muted-foreground">{hint}</p>
        {note ? <p className="mt-1 text-xs text-muted-foreground">{note}</p> : null}
      </div>
    );
  }
  return (
    <div className="rounded-lg border border-dashed border-border bg-surface p-4">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium leading-snug">Gizi (estimasi porsi)</p>
        <p className="shrink-0 text-sm font-semibold">{value}</p>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface-overlay">
        <div
          className="h-full rounded-full bg-brand-500"
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
      {note ? <p className="mt-2 text-xs text-muted-foreground">{note}</p> : null}
    </div>
  );
}
