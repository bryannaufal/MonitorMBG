import { api } from "@/lib/api";

const STORAGE_KEY = "mbg.scrapeJob.v1";
const POLL_MS = 800;

export type ScrapePhase = "idle" | "fetching" | "scoring" | "done" | "error";

export interface ScrapeJobStatus {
  active: boolean;
  job_id?: string;
  phase: ScrapePhase;
  label?: string;
  current?: number;
  total?: number;
  mode?: string;
  auto_ticket?: boolean;
  result?: {
    message?: string;
    inserted?: number;
    intake_origin?: string;
  };
  error?: string;
}

type Listener = (status: ScrapeJobStatus) => void;

let pollTimer: ReturnType<typeof setInterval> | null = null;
let listeners = new Set<Listener>();
let lastStatus: ScrapeJobStatus = { active: false, phase: "idle" };

function persist(status: ScrapeJobStatus): void {
  if (typeof window === "undefined") return;
  try {
    if (status.active || status.phase === "done" || status.phase === "error") {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(status));
    } else {
      sessionStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    /* abaikan */
  }
}

export function readStoredScrapeStatus(): ScrapeJobStatus | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as ScrapeJobStatus;
  } catch {
    return null;
  }
}

function notify(status: ScrapeJobStatus): void {
  lastStatus = status;
  persist(status);
  for (const fn of listeners) fn(status);
}

export function getScrapeStatus(): ScrapeJobStatus {
  return lastStatus;
}

export function subscribeScrape(listener: Listener): () => void {
  listeners.add(listener);
  listener(lastStatus);
  return () => {
    listeners.delete(listener);
  };
}

function stopPolling(): void {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function pollOnce(): Promise<ScrapeJobStatus> {
  const status = await api.get<ScrapeJobStatus>("/intake/scrape/status");
  notify(status);
  if (!status.active && status.phase !== "fetching" && status.phase !== "scoring") {
    stopPolling();
  }
  return status;
}

function startPolling(): void {
  if (pollTimer) return;
  pollTimer = setInterval(() => {
    pollOnce().catch(() => {
      notify({
        active: false,
        phase: "error",
        error: "Tidak dapat membaca status scrape — pastikan backend berjalan.",
        label: "Scrape gagal",
      });
      stopPolling();
    });
  }, POLL_MS);
}

export async function startScrape(): Promise<ScrapeJobStatus> {
  const status = await api.post<ScrapeJobStatus, Record<string, never>>("/intake/scrape", {});
  notify(status);
  if (status.phase === "fetching" || status.phase === "scoring" || status.active) {
    startPolling();
    pollOnce().catch(() => undefined);
  }
  return status;
}

export function resumeScrapePolling(): void {
  const stored = readStoredScrapeStatus();
  if (stored) {
    lastStatus = stored;
    for (const fn of listeners) fn(stored);
  }
  if (
    stored?.phase === "fetching" ||
    stored?.phase === "scoring" ||
    (stored?.active && stored.phase !== "done" && stored.phase !== "error")
  ) {
    startPolling();
    pollOnce().catch(() => undefined);
  }
}

export function clearScrapeSession(): void {
  stopPolling();
  lastStatus = { active: false, phase: "idle" };
  if (typeof window !== "undefined") {
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      /* abaikan */
    }
  }
}

export function isScrapeBusy(status: ScrapeJobStatus = lastStatus): boolean {
  return status.phase === "fetching" || status.phase === "scoring";
}
