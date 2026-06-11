"use client";

import { Clock, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";

interface TicketCardProps {
  source: string;
  severity: string;
  title: string;
  time: string;
}

export default function TicketCard({ source, severity, title, time }: TicketCardProps) {
  const severityColors = {
    high: "border-severity-high bg-severity-high/10 text-severity-high",
    medium: "border-severity-medium bg-severity-medium/10 text-severity-medium",
    low: "border-severity-low bg-severity-low/10 text-severity-low",
    critical: "border-severity-critical bg-severity-critical/10 text-severity-critical",
  } as Record<string, string>;

  const colorClass = severityColors[severity] || severityColors.low;

  return (
    <div className="group min-w-0 rounded-lg border border-border bg-surface p-4 transition-shadow hover:shadow-md">
      <div className="mb-2 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <span className="break-words text-xs font-semibold uppercase text-muted-foreground">{source}</span>
          <span className={cn("rounded-full border px-2 py-0.5 text-[10px] uppercase", colorClass)}>
            {severity}
          </span>
        </div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          {time}
        </div>
      </div>
      <h4 className="mb-3 line-clamp-2 break-words text-sm font-medium text-foreground">{title}</h4>
      <div className="mt-auto flex items-center justify-between gap-3">
        <button className="text-xs flex items-center gap-1 text-brand-500 hover:text-brand-600 transition-colors">
          View Details
        </button>
        <button className="opacity-0 group-hover:opacity-100 transition-opacity">
          <ExternalLink className="h-4 w-4 text-muted-foreground hover:text-foreground" />
        </button>
      </div>
    </div>
  );
}
