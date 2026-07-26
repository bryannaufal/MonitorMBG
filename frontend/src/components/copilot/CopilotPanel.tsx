"use client";

import { useState } from "react";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import { Bot, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { overlayCases } from "@/lib/runtimeOverlay";
import type { CopilotResponse, CopilotSource } from "@/types/monitoring";

interface Message {
  id: string;
  role: "assistant" | "user";
  content: string;
  sources?: CopilotSource[];
}

const suggestedQuestions = [
  "Kasus mana yang prioritas tertinggi hari ini?",
  "Ringkas kasus berisiko tertinggi.",
  "Mengapa vendor ini masuk daftar pantauan?",
  "Bukti apa yang mendukung kasus ini?",
  "Apa langkah berikutnya untuk operator?",
  "Tampilkan anomali gizi.",
  "Wilayah mana yang paling berisiko?",
  "Jelaskan hasil penilaian.",
];

export default function CopilotPanel() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Halo, saya Asisten Ringkasan Kasus MonitorMBG (terbatas). Tanyakan tentang kasus prioritas, alasan daftar pantauan vendor, bukti, anomali gizi, wilayah, atau langkah tindak lanjut yang disarankan.",
    },
  ]);
  const [loading, setLoading] = useState(false);

  const handleSend = async (text: string) => {
    setMessages((prev) => [...prev, { id: Date.now().toString(), role: "user", content: text }]);
    setLoading(true);
    try {
      const response = await api.post<
        CopilotResponse,
        { message: string; client_cases?: ReturnType<typeof overlayCases> }
      >("/copilot/chat", {
        message: text,
        client_cases: overlayCases(),
      });
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
            "Saya tidak dapat menjangkau layanan asisten backend saat ini. Panduan offline: tinjau tiket Kritis dan Tinggi lebih dulu, verifikasi paket bukti, dan catat semua keputusan operator di jejak audit.\n\nSintesis berbantuan AI, memerlukan tinjauan operator.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex h-full min-w-0 flex-col bg-surface">
      <div className="flex min-w-0 items-center gap-3 border-b border-border bg-surface-raised p-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-500/20 text-brand-500">
          <Bot className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <h2 className="break-words text-lg font-semibold">Asisten Ringkasan Kasus</h2>
          <p className="break-words text-xs text-brand-400">Sintesis terbatas &bull; sumber internal</p>
        </div>
      </div>
      <div className="border-b border-border bg-brand-500/10 px-4 py-3 text-xs text-brand-800 dark:text-brand-100">
        <div className="flex items-start gap-2">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-brand-300" />
          <span className="min-w-0 break-words">Sintesis berbantuan AI, memerlukan tinjauan operator. RAG memakai Gemini bila key tersedia; fallback embedding lokal tanpa API. Chat sintesis memakai Kimi.</span>
        </div>
      </div>
      <div className="border-b border-border bg-surface-raised px-4 py-3">
        <div className="flex gap-2 overflow-x-auto pb-1 sm:flex-wrap sm:overflow-visible sm:pb-0">
          {suggestedQuestions.map((question) => (
            <button
              key={question}
              onClick={() => handleSend(question)}
              disabled={loading}
              className="shrink-0 rounded-full border border-border bg-surface px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-brand-500/60 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-60 sm:whitespace-normal"
            >
              {question}
            </button>
          ))}
        </div>
      </div>
      
      <div className="min-w-0 flex-1 space-y-6 overflow-y-auto p-3 sm:p-4">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} role={msg.role} content={msg.content} sources={msg.sources} />
        ))}
        {loading ? (
          <ChatMessage role="assistant" content="Menyusun ringkasan dari sumber internal..." />
        ) : null}
      </div>

      <div className="border-t border-border bg-surface-raised p-3 sm:p-4">
        <ChatInput onSend={handleSend} />
      </div>
    </div>
  );
}
