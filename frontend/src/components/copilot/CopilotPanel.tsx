"use client";

import { useState } from "react";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import { Bot, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import type { CopilotResponse, CopilotSource } from "@/types/monitoring";

interface Message {
  id: string;
  role: "assistant" | "user";
  content: string;
  sources?: CopilotSource[];
}

const suggestedQuestions = [
  "Which cases are highest priority today?",
  "Summarize the highest risk case.",
  "Why is this vendor on the watchlist?",
  "What evidence supports this case?",
  "What should the operator do next?",
  "Show nutrition anomalies.",
  "Which region has the highest risk?",
  "Explain the scoring result.",
];

export default function CopilotPanel() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hello, I'm your bounded MonitorMBG AI Copilot. Ask about priority cases, vendor watchlist reasons, evidence, nutrition anomalies, regions, or recommended next steps.",
    },
  ]);
  const [loading, setLoading] = useState(false);

  const handleSend = async (text: string) => {
    setMessages((prev) => [...prev, { id: Date.now().toString(), role: "user", content: text }]);
    setLoading(true);
    try {
      const response = await api.post<CopilotResponse, { message: string }>("/copilot/chat", { message: text });
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: response.answer,
          sources: response.sources,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content:
            "I cannot reach the backend copilot service right now. Demo fallback guidance: review Critical and High tickets first, verify evidence packages, and record all operator decisions in the audit trail.\n\nAI-assisted synthesis, operator review required.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-surface relative">
      <div className="p-4 border-b border-border bg-surface-raised flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-500">
          <Bot className="h-5 w-5" />
        </div>
        <div>
          <h2 className="font-semibold text-lg">AI Copilot</h2>
          <p className="text-xs text-brand-400">Bounded demo synthesis &bull; internal demo sources</p>
        </div>
      </div>
      <div className="border-b border-border bg-brand-500/10 px-4 py-3 text-xs text-brand-100">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-brand-300" />
          AI-assisted synthesis, operator review required. No external API is called by default.
        </div>
      </div>
      <div className="border-b border-border bg-surface-raised px-4 py-3">
        <div className="flex flex-wrap gap-2">
          {suggestedQuestions.map((question) => (
            <button
              key={question}
              onClick={() => handleSend(question)}
              disabled={loading}
              className="rounded-full border border-border bg-surface px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-brand-500/60 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-60"
            >
              {question}
            </button>
          ))}
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} role={msg.role} content={msg.content} sources={msg.sources} />
        ))}
        {loading ? (
          <ChatMessage role="assistant" content="Synthesizing from internal demo sources..." />
        ) : null}
      </div>

      <div className="p-4 bg-surface-raised border-t border-border">
        <ChatInput onSend={handleSend} />
      </div>
    </div>
  );
}
