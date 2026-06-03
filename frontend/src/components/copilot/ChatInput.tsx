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
    <div className="relative flex items-center w-full">
      <button className="absolute left-3 p-2 text-muted-foreground hover:text-foreground transition-colors rounded-full hover:bg-surface">
        <Paperclip className="h-4 w-4" />
      </button>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask the copilot anything..."
        className="w-full pl-12 pr-12 py-3 bg-surface border border-border rounded-full text-sm focus:outline-none focus:ring-1 focus:ring-brand-500 shadow-sm"
      />
      <button
        onClick={handleSend}
        disabled={!text.trim()}
        className="absolute right-2 p-2 bg-brand-500 text-white rounded-full hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <Send className="h-4 w-4" />
      </button>
    </div>
  );
}
