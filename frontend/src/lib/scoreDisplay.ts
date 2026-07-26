import type { OversightCase, ScoreResult } from "@/types/monitoring";

/** Skor numerik untuk tampilan; hilangkan `undefined` di UI. */
export function fmtScore(value: number | null | undefined, fallback = 0): string {
  return String(value ?? fallback);
}

/** Gizi: strip bila belum dinilai (bukan 0 — nol artinya gizi buruk). */
export function fmtGizi(value: number | null | undefined): string {
  return value == null ? "—" : String(value);
}

export function normalizeScore(score: ScoreResult | null | undefined): ScoreResult {
  if (!score) {
    return {
      id: 0,
      case_id: "",
      vendor_id: "",
      vendor_name: "",
      region: "",
      severity_score: 0,
      confidence_score: 0,
      actionability_score: 0,
      nutrition_score: null,
      final_priority_score: 0,
      priority_label: "Rendah",
      explanation: "",
      recommended_action: "",
      computed_at: "",
      ai_notice: "",
    };
  }
  return {
    ...score,
    severity_score: score.severity_score ?? 0,
    confidence_score: score.confidence_score ?? 0,
    actionability_score: score.actionability_score ?? 0,
    nutrition_score: score.nutrition_score ?? null,
    final_priority_score: score.final_priority_score ?? 0,
  };
}

export function normalizeCase(item: OversightCase): OversightCase {
  return { ...item, score: normalizeScore(item.score) };
}
