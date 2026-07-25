"use client";

import { useState } from "react";
import { Send, Paperclip } from "lucide-react";

interface ChatInputProps {
  onSend: (text: string) => void;
}

export default function ChatInput({ onSend }: ChatInputProps) {
  const [text, setText] = useState("");

  const handleSend = () => {
    if (text.trim()) {
      onSend(text.trim());
      setText("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="relative flex min-w-0 w-full items-center">
      <button className="absolute left-2 rounded-full p-2 text-muted-foreground transition-colors hover:bg-surface hover:text-foreground sm:left-3">
        <Paperclip className="h-4 w-4" />
      </button>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Tanyakan apa saja ke asisten..."
        className="w-full min-w-0 rounded-full border border-border bg-surface py-3 pl-11 pr-12 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-brand-500 sm:pl-12"
      />
      <button
        onClick={handleSend}
        disabled={!text.trim()}
        className="absolute right-2 rounded-full bg-brand-500 p-2 text-white transition-colors hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Send className="h-4 w-4" />
      </button>
    </div>
  );
}
