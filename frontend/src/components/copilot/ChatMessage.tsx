"use client";

import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";
import type { CopilotSource } from "@/types/monitoring";

interface ChatMessageProps {
  role: string;
  content: string;
  sources?: CopilotSource[];
}

export default function ChatMessage({ role, content, sources = [] }: ChatMessageProps) {
  const isAssistant = role === "assistant";

  return (
    <div className={cn("flex gap-4 w-full", isAssistant ? "justify-start" : "justify-end")}>
      {isAssistant && (
        <div className="h-8 w-8 rounded-full bg-brand-500/20 flex items-center justify-center shrink-0 text-brand-500">
          <Bot className="h-4 w-4" />
        </div>
      )}
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isAssistant
            ? "bg-surface-overlay text-foreground rounded-tl-none border border-border"
            : "bg-brand-600 text-white rounded-tr-none"
        )}
      >
        <p className="whitespace-pre-line">{content}</p>
        {sources.length > 0 ? (
          <div className="mt-3 space-y-2 border-t border-border/60 pt-3">
            <p className="text-xs font-semibold uppercase text-muted-foreground">Sources</p>
            {sources.map((source) => (
              <div key={`${source.source_type}-${source.source_id}`} className="rounded-md bg-surface/60 px-3 py-2 text-xs">
                <p className="font-medium">{source.title}</p>
                {source.content_snippet ? <p className="mt-1 text-muted-foreground">{source.content_snippet}</p> : null}
                <p className="mt-1 text-muted-foreground">
                  {source.source_type} · relevance {(source.relevance_score * 100).toFixed(0)}%
                </p>
              </div>
            ))}
          </div>
        ) : null}
      </div>
      {!isAssistant && (
        <div className="h-8 w-8 rounded-full bg-surface-overlay flex items-center justify-center shrink-0 border border-border">
          <User className="h-4 w-4 text-muted-foreground" />
        </div>
      )}
    </div>
  );
}
