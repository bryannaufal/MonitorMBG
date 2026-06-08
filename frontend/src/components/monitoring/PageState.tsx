"use client";

export function LoadingState({ label = "Loading demo intelligence..." }: { label?: string }) {
  return (
    <div className="min-w-0 rounded-lg border border-border bg-surface-raised p-4 text-sm text-muted-foreground sm:p-6">
      {label}
    </div>
  );
}

export function SourceState({ source, error }: { source: "api" | "fallback"; error?: string }) {
  if (source === "api") {
    return (
      <span className="inline-flex max-w-full rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
        Live demo API
      </span>
    );
  }

  return (
    <span
      className="inline-flex max-w-full rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs text-amber-300"
      title={error}
    >
      Fallback demo data
    </span>
  );
}
