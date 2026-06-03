"use client";

import CopilotPanel from "@/components/copilot/CopilotPanel";

export default function CopilotPage() {
  return (
    <div className="h-full flex flex-col space-y-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Copilot</h1>
        <p className="text-muted-foreground">
          RAG-based assistant for operational intelligence and case synthesis.
        </p>
      </div>
      <div className="flex-1 bg-surface-raised border rounded-xl overflow-hidden shadow-sm">
        <CopilotPanel />
      </div>
    </div>
  );
}
