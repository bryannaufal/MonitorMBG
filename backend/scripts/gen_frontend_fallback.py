"""Hasilkan `frontend/src/lib/demoFallback.ts` dari sumber kanonik.

Fallback frontend WAJIB identik dengan data yang disajikan backend & di-seed
ke DB. Alih-alih menyalin manual (rawan divergen), file ini dibangkitkan dari
``app.demo_data`` (yang menurunkan semuanya dari ``app.seed_data``).

    python -m scripts.gen_frontend_fallback

Jalankan ulang setiap kali ``seed_data`` berubah.
"""

from __future__ import annotations

import json
from pathlib import Path

from app import demo_data as d

OUT = Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "demoFallback.ts"


def js(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def build() -> str:
    cases = d.oversight_cases()
    overview = d.overview()
    nutrition_summary = {
        "avg_calories": 512,
        "avg_protein_g": 14.0,
        "avg_carbs_g": 63,
        "avg_fat_g": 11.5,
        "total_reports_analyzed": len(d.DAILY_REPORTS),
        "flagged_reports": [r for r in d.DAILY_REPORTS if r["mismatch_indicator"] or r["cost_estimate"]["cost_anomaly_flag"]],
        "ai_notice": d.DEMO_NOTICE,
    }

    blocks = {
        "demoNotice": json.dumps(d.DEMO_NOTICE, ensure_ascii=False),
        "fallbackOverview": js(overview),
        "fallbackVendors": js(d.VENDORS),
        "fallbackLocationRegistry": js(d.LOCATION_REGISTRY),
        "fallbackInvestigators": js(d.INVESTIGATOR_REGISTRY),
        "fallbackUnits": js(d.UNIT_REGISTRY),
        "fallbackSignals": js(d.SIGNALS),
        "fallbackComplaints": js(d.COMPLAINTS),
        "fallbackReports": js(d.REPORTS),
        "fallbackDailyReports": js(d.DAILY_REPORTS),
        "fallbackEvidence": js(d.EVIDENCE),
        "fallbackScores": js(d.SCORES),
        "fallbackTickets": js(d.TICKETS),
        "fallbackAudit": js(d.AUDIT_TRAIL),
        "fallbackCases": js(cases),
        "fallbackHeatmap": js(d.REGIONAL_HEATMAP),
        "fallbackTrends": js(d.TRENDS),
        "fallbackAnomalies": js(d.ANOMALIES),
        "fallbackNutritionSummary": js(nutrition_summary),
    }

    type_names = [
        "AnalyticsOverview", "AnomalyHighlight", "AssignmentCandidate", "AuditTrailEvent", "Complaint", "DailyReport",
        "Evidence", "HeatmapRegion", "ListResponse", "NutritionSummary", "OversightCase", "Report",
        "ScoreResult", "Signal", "Ticket", "TrendPoint", "Vendor", "LocationRegistryEntry",
    ]
    import_body = "\n".join(f"  {name}," for name in type_names)
    type_map = {
        "fallbackOverview": "AnalyticsOverview",
        "fallbackVendors": "Vendor[]",
        "fallbackLocationRegistry": "LocationRegistryEntry[]",
        "fallbackInvestigators": "AssignmentCandidate[]",
        "fallbackUnits": "AssignmentCandidate[]",
        "fallbackSignals": "Signal[]",
        "fallbackComplaints": "Complaint[]",
        "fallbackReports": "Report[]",
        "fallbackDailyReports": "DailyReport[]",
        "fallbackEvidence": "Evidence[]",
        "fallbackScores": "ScoreResult[]",
        "fallbackTickets": "Ticket[]",
        "fallbackAudit": "AuditTrailEvent[]",
        "fallbackCases": "OversightCase[]",
        "fallbackHeatmap": "HeatmapRegion[]",
        "fallbackTrends": "TrendPoint[]",
        "fallbackAnomalies": "AnomalyHighlight[]",
        "fallbackNutritionSummary": "NutritionSummary",
    }

    lines = [
        "// FILE DIBANGKITKAN OTOMATIS — jangan diedit manual.",
        "// Sumber: backend/app/seed_data.py (via scripts/gen_frontend_fallback.py).",
        "// Cermin identik dengan data API & seed DB (mode offline).",
        "import type {\n" + import_body + "\n} from \"@/types/monitoring\";",
        "",
        f"export const demoNotice = {blocks['demoNotice']};",
        "",
    ]
    for name, payload in blocks.items():
        if name == "demoNotice":
            continue
        lines.append(f"export const {name}: {type_map[name]} = {payload};")
        lines.append("")

    lines.append("export const asList = <T>(items: T[]): ListResponse<T> => ({")
    lines.append("  items,")
    lines.append("  total: items.length,")
    lines.append("  page: 1,")
    lines.append("  size: items.length,")
    lines.append("});")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"✓ Ditulis: {OUT}")
