"use client";

import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";

interface ChatMessageProps {
  role: string;
  content: string;
}

export default function ChatMessage({ role, content }: ChatMessageProps) {
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
        {content}
      </div>
      {!isAssistant && (
        <div className="h-8 w-8 rounded-full bg-surface-overlay flex items-center justify-center shrink-0 border border-border">
          <User className="h-4 w-4 text-muted-foreground" />
        </div>
      )}
    </div>
  );
}
