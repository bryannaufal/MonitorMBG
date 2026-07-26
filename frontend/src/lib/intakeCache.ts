import type { Signal } from "@/types/monitoring";

const KEY = "mbg.intakePage.v1";

export interface IntakePageCache {
  signals: Signal[];
  caseStatus: Record<string, string>;
  casePriority: Record<string, number>;
  source: "api" | "fallback";
  error?: string;
  savedAt: number;
}

export function readIntakeCache(): IntakePageCache | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return null;
    return JSON.parse(raw) as IntakePageCache;
  } catch {
    return null;
  }
}

export function writeIntakeCache(data: Omit<IntakePageCache, "savedAt">): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(KEY, JSON.stringify({ ...data, savedAt: Date.now() }));
  } catch {
    /* abaikan */
  }
}
