import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** `case-001` -> `MBG-001` (nomor kasus ramah pengguna). */
export function caseNumber(caseId: string): string {
  const digits = caseId.replace(/\D/g, "") || "000";
  return `MBG-${digits}`;
}
