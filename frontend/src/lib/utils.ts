import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** `case-001` -> `MBG-001` (nomor kasus ramah pengguna). */
export function caseNumber(caseId: string | null | undefined): string {
  if (!caseId) return "—";
  const digits = caseId.replace(/\D/g, "") || "000";
  return `MBG-${digits}`;
}

/** `/evidence-media/foo.jpg` -> URL statis backend (dataset foto bukti). */
export function evidenceMediaUrl(path: string | null | undefined): string | undefined {
  if (!path) return undefined;
  if (/^https?:\/\//i.test(path)) return path;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  const origin = apiUrl.replace(/\/api\/v1\/?$/, "");
  return `${origin}${path.startsWith("/") ? path : `/${path}`}`;
}
