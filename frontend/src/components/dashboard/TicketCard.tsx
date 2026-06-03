"use client";

import { AlertCircle, Clock, ExternalLink } from "lucide-react";
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
    <div className="bg-surface border border-border rounded-lg p-4 hover:shadow-md transition-shadow group">
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-muted-foreground uppercase">{source}</span>
          <span className={cn("text-[10px] uppercase px-2 py-0.5 rounded-full border", colorClass)}>
            {severity}
          </span>
        </div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          {time}
        </div>
      </div>
      <h4 className="font-medium text-sm text-foreground line-clamp-2 mb-3">{title}</h4>
      <div className="flex justify-between items-center mt-auto">
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
