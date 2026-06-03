"use client";

import { useState } from "react";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import { Bot } from "lucide-react";

export default function CopilotPanel() {
  const [messages, setMessages] = useState([
    {
      id: "1",
      role: "assistant",
      content: "Hello, I'm your MonitorMBG AI Copilot. How can I help you analyze reports or investigate issues today?",
    },
  ]);

  const handleSend = (text: string) => {
    setMessages((prev) => [...prev, { id: Date.now().toString(), role: "user", content: text }]);
    // Mock response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "I'm looking into that for you. Based on recent data, there's a noted anomaly in Jakarta Selatan...",
        },
      ]);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-full bg-surface relative">
      <div className="p-4 border-b border-border bg-surface-raised flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-500">
          <Bot className="h-5 w-5" />
        </div>
        <div>
          <h2 className="font-semibold text-lg">AI Copilot</h2>
          <p className="text-xs text-brand-400">Online &bull; RAG Enabled</p>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} role={msg.role} content={msg.content} />
        ))}
      </div>

      <div className="p-4 bg-surface-raised border-t border-border">
        <ChatInput onSend={handleSend} />
      </div>
    </div>
  );
}
