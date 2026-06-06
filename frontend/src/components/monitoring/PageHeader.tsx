"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { ChevronRight } from "lucide-react";

import { cn } from "@/lib/utils";
import { SourceState } from "./PageState";

interface Breadcrumb {
  label: string;
  href?: string;
}

export function PageHeader({
  title,
  description,
  breadcrumbs = [],
  action,
  source,
  error,
}: {
  title: string;
  description: string;
  breadcrumbs?: Breadcrumb[];
  action?: ReactNode;
  source?: "api" | "fallback";
  error?: string;
}) {
  return (
    <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        {breadcrumbs.length ? (
          <nav className="mb-2 flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
            {breadcrumbs.map((item, index) => (
              <span key={`${item.label}-${index}`} className="inline-flex items-center gap-1">
                {item.href ? (
                  <Link href={item.href} className="hover:text-brand-300">
                    {item.label}
                  </Link>
                ) : (
                  <span>{item.label}</span>
                )}
                {index < breadcrumbs.length - 1 ? <ChevronRight className="h-3 w-3" /> : null}
              </span>
            ))}
          </nav>
        ) : null}
        <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
        <p className="mt-1 max-w-3xl text-muted-foreground">{description}</p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {action}
        {source ? <SourceState source={source} error={error} /> : null}
      </div>
    </div>
  );
}

export function HelperPanel({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-lg border border-brand-500/25 bg-brand-500/10 p-4 text-sm leading-6 text-brand-100">
      {children}
    </div>
  );
}

export function MetricTile({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 text-xl font-semibold">{value}</p>
      {detail ? <p className="mt-1 text-xs text-muted-foreground">{detail}</p> : null}
    </div>
  );
}

export function EntityChip({
  label,
  href,
  tone = "default",
}: {
  label: string;
  href?: string;
  tone?: "default" | "case" | "vendor" | "ticket" | "evidence" | "score" | "audit";
}) {
  const toneClass = {
    default: "border-border bg-surface-overlay text-muted-foreground",
    case: "border-brand-500/40 bg-brand-500/10 text-brand-200",
    vendor: "border-emerald-500/35 bg-emerald-500/10 text-emerald-200",
    ticket: "border-sky-500/35 bg-sky-500/10 text-sky-200",
    evidence: "border-amber-500/35 bg-amber-500/10 text-amber-200",
    score: "border-orange-500/35 bg-orange-500/10 text-orange-200",
    audit: "border-violet-500/35 bg-violet-500/10 text-violet-200",
  }[tone];
  const className = cn("inline-flex rounded-full border px-2.5 py-1 text-xs font-medium", toneClass);

  if (href) {
    return (
      <Link href={href} className={cn(className, "transition-colors hover:border-brand-300")}>
        {label}
      </Link>
    );
  }

  return <span className={className}>{label}</span>;
}
