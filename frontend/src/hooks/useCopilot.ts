import { useState } from "react";
import { api } from "@/lib/api";

export function useCopilot() {
  const [loading, setLoading] = useState(false);

  const sendMessage = async (message: string) => {
    setLoading(true);
    try {
      // const res = await api.post("/copilot/chat", { message });
      // return res.answer;
      return "Placeholder copilot response.";
    } catch (error) {
      console.error("Copilot error", error);
      return "Error reaching copilot.";
    } finally {
      setLoading(false);
    }
  };

  return { sendMessage, loading };
}
