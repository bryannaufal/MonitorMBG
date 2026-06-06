"""Deterministic MonitorMBG demo dataset and helper queries.

The MVP intentionally uses fictional, privacy-safe Indonesian supervision
scenarios. AI/CV/OCR/RAG fields are simulated pre-verification signals for
operator review, not autonomous findings.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

DEMO_NOTICE = (
    "AI-assisted pre-verification signal. Final decisions remain with "
    "authorized government operators."
)


def _ts(day: int, hour: int, minute: int = 0) -> str:
    return datetime(2026, 6, day, hour, minute, tzinfo=timezone.utc).isoformat()


VENDORS: list[dict[str, Any]] = [
    {
        "id": "vnd-001",
        "name": "SPPG Gizi Nusantara Selatan",
        "region": "DKI Jakarta",
        "district": "Jakarta Selatan",
        "assigned_schools": ["SDN Pejaten 03", "SMPN 182 Jakarta", "SDN Ragunan 07"],
        "daily_meal_volume": 3280,
        "compliance_status": "Under Review",
        "risk_score": 88,
        "risk_trend": [62, 68, 74, 81, 88],
        "watchlist_status": "Critical",
        "watchlist_reason": "Repeated low protein complaints, late delivery, and duplicate photo suspicion.",
        "last_inspection_date": "2026-05-29",
        "repeated_issue_categories": ["low protein portion", "delayed delivery", "duplicate photo"],
        "coverage_notes": "Three schools in South Jakarta cluster; high public-signal density this week.",
        "recommended_action": "Escalate field verification within 24 hours and request replacement evidence.",
    },
    {
        "id": "vnd-002",
        "name": "Dapur Sehat Bandung Raya",
        "region": "Jawa Barat",
        "district": "Kota Bandung",
        "assigned_schools": ["SDN Sukajadi 05", "SMPN 12 Bandung"],
        "daily_meal_volume": 2410,
        "compliance_status": "Needs Verification",
        "risk_score": 79,
        "risk_trend": [52, 56, 63, 72, 79],
        "watchlist_status": "High",
        "watchlist_reason": "Hygiene concern and suspected food poisoning signals from two independent channels.",
        "last_inspection_date": "2026-05-25",
        "repeated_issue_categories": ["hygiene concern", "suspected food poisoning", "cold food"],
        "coverage_notes": "Two nearby schools reported similar symptoms within 48 hours.",
        "recommended_action": "Coordinate health office inspection and temporarily increase sampling.",
    },
    {
        "id": "vnd-003",
        "name": "SPPG Pangan Aman Semarang",
        "region": "Jawa Tengah",
        "district": "Kota Semarang",
        "assigned_schools": ["SDN Tembalang 01", "SMPN 21 Semarang"],
        "daily_meal_volume": 1980,
        "compliance_status": "Compliant",
        "risk_score": 34,
        "risk_trend": [38, 36, 34, 33, 34],
        "watchlist_status": "Low",
        "watchlist_reason": "Routine monitoring only.",
        "last_inspection_date": "2026-05-31",
        "repeated_issue_categories": ["documentation incomplete"],
        "coverage_notes": "Stable operations with minor documentation gaps.",
        "recommended_action": "Request completion of delivery checklist in next daily report.",
    },
    {
        "id": "vnd-004",
        "name": "Dapur Mandiri Surabaya Timur",
        "region": "Jawa Timur",
        "district": "Surabaya",
        "assigned_schools": ["SDN Rungkut Menanggal", "SMPN 35 Surabaya"],
        "daily_meal_volume": 2875,
        "compliance_status": "Escalated",
        "risk_score": 83,
        "risk_trend": [55, 61, 70, 77, 83],
        "watchlist_status": "Critical",
        "watchlist_reason": "Cost anomaly, missing fruit/milk, and repeated menu mismatch.",
        "last_inspection_date": "2026-05-22",
        "repeated_issue_categories": ["cost anomaly", "missing fruit/milk", "menu mismatch"],
        "coverage_notes": "Reported cost per portion above benchmark while menu completeness declined.",
        "recommended_action": "Escalate to procurement review and conduct menu verification.",
    },
    {
        "id": "vnd-005",
        "name": "SPPG Cerdas Gizi Medan",
        "region": "Sumatera Utara",
        "district": "Kota Medan",
        "assigned_schools": ["SDN Medan Johor 09", "SMPN 28 Medan"],
        "daily_meal_volume": 1740,
        "compliance_status": "Compliant",
        "risk_score": 41,
        "risk_trend": [43, 39, 40, 42, 41],
        "watchlist_status": "Medium",
        "watchlist_reason": "Cold food complaints remain below escalation threshold.",
        "last_inspection_date": "2026-05-30",
        "repeated_issue_categories": ["cold food", "delayed delivery"],
        "coverage_notes": "Issue appears operational, not evidence-fraud related.",
        "recommended_action": "Monitor delivery route timing for one week.",
    },
    {
        "id": "vnd-006",
        "name": "Dapur Prima Makassar",
        "region": "Sulawesi Selatan",
        "district": "Makassar",
        "assigned_schools": ["SDN Panakkukang 02", "SMPN 8 Makassar"],
        "daily_meal_volume": 2135,
        "compliance_status": "Needs Verification",
        "risk_score": 67,
        "risk_trend": [45, 51, 56, 63, 67],
        "watchlist_status": "High",
        "watchlist_reason": "Documentation incomplete and low confidence evidence package.",
        "last_inspection_date": "2026-05-27",
        "repeated_issue_categories": ["documentation incomplete", "menu mismatch"],
        "coverage_notes": "Daily report images are complete but invoice OCR fields are weak.",
        "recommended_action": "Request corrected invoice and operator review of evidence.",
    },
    {
        "id": "vnd-007",
        "name": "SPPG Sejahtera Denpasar",
        "region": "Bali",
        "district": "Denpasar",
        "assigned_schools": ["SDN Renon 04", "SMPN 10 Denpasar"],
        "daily_meal_volume": 1320,
        "compliance_status": "Compliant",
        "risk_score": 28,
        "risk_trend": [31, 30, 29, 27, 28],
        "watchlist_status": "Low",
        "watchlist_reason": "No repeated high-risk issue.",
        "last_inspection_date": "2026-06-01",
        "repeated_issue_categories": [],
        "coverage_notes": "Stable vendor with complete daily documentation.",
        "recommended_action": "Continue routine monitoring.",
    },
    {
        "id": "vnd-008",
        "name": "Dapur Anak Hebat Yogyakarta",
        "region": "DI Yogyakarta",
        "district": "Sleman",
        "assigned_schools": ["SDN Condongcatur 02", "SMPN 4 Sleman"],
        "daily_meal_volume": 1565,
        "compliance_status": "Under Review",
        "risk_score": 58,
        "risk_trend": [35, 42, 46, 53, 58],
        "watchlist_status": "Medium",
        "watchlist_reason": "Rising missing fruit reports and one public anomaly spike.",
        "last_inspection_date": "2026-05-28",
        "repeated_issue_categories": ["missing fruit/milk", "documentation incomplete"],
        "coverage_notes": "Recent trend is rising but evidence confidence is moderate.",
        "recommended_action": "Review next three daily reports and confirm menu substitutions.",
    },
]

_vendor_lookup = {vendor["id"]: vendor for vendor in VENDORS}


ISSUES = [
    ("suspected food poisoning", "negative", 96),
    ("delayed delivery", "negative", 62),
    ("low protein portion", "negative", 78),
    ("menu mismatch", "negative", 70),
    ("hygiene concern", "negative", 88),
    ("duplicate photo", "neutral", 74),
    ("cold food", "negative", 55),
    ("missing fruit/milk", "negative", 64),
    ("cost anomaly", "neutral", 82),
    ("documentation incomplete", "neutral", 48),
]

COMPLAINTS: list[dict[str, Any]] = []
for idx in range(1, 21):
    issue, sentiment, severity = ISSUES[(idx - 1) % len(ISSUES)]
    vendor = VENDORS[(idx - 1) % len(VENDORS)]
    channel = ["Twitter/X", "Instagram", "School Hotline", "Parent Form", "Community Report"][idx % 5]
    COMPLAINTS.append(
        {
            "id": idx,
            "case_id": f"case-{((idx - 1) % 10) + 1:03d}",
            "source": channel,
            "source_confidence": round(0.58 + ((idx % 7) * 0.055), 2),
            "summary": f"{issue.title()} reported near {vendor['assigned_schools'][0]}",
            "text": (
                f"Fictional demo signal: warga melaporkan {issue} pada distribusi MBG "
                f"oleh {vendor['name']}."
            ),
            "issue_category": issue,
            "sentiment": sentiment,
            "severity_score": min(100, severity + (idx % 4) * 2),
            "region": vendor["region"],
            "district": vendor["district"],
            "school": vendor["assigned_schools"][0],
            "vendor_id": vendor["id"],
            "vendor_name": vendor["name"],
            "status": ["New", "Under Review", "Triaged", "Linked to Ticket"][idx % 4],
            "anomaly_tag": "Spike" if idx in {1, 2, 5, 11, 14} else None,
            "created_at": _ts(1 + (idx % 4), 7 + (idx % 10), 15),
        }
    )

REPORTS: list[dict[str, Any]] = [
    {
        "id": idx,
        "case_id": f"case-{idx:03d}",
        "report_code": f"RPT-MBG-2026-{idx:03d}",
        "reporter_type": ["School Operator", "Public Complaint Desk", "District Supervisor"][idx % 3],
        "school": vendor["assigned_schools"][0],
        "region": vendor["region"],
        "district": vendor["district"],
        "vendor_id": vendor["id"],
        "vendor_name": vendor["name"],
        "submitted_at": _ts(1 + (idx % 5), 9 + idx, 20),
        "summary": f"Official report package for {vendor['name']} covering menu delivery and evidence review.",
        "evidence_count": 2 + (idx % 4),
        "status": ["Under Review", "Escalated", "Needs Evidence", "Resolved"][idx % 4],
        "completeness_score": max(45, 94 - idx * 4),
        "linked_ticket_id": f"tkt-{idx:03d}",
        "linked_risk_score": vendor["risk_score"],
    }
    for idx, vendor in enumerate(VENDORS + VENDORS[:2], start=1)
]

DAILY_REPORTS: list[dict[str, Any]] = [
    {
        "id": idx,
        "case_id": f"case-{idx:03d}",
        "vendor_id": vendor["id"],
        "vendor_name": vendor["name"],
        "school": vendor["assigned_schools"][idx % len(vendor["assigned_schools"])],
        "region": vendor["region"],
        "planned_menu": "Nasi, ayam, sayur, buah, susu",
        "actual_menu": [
            "Nasi, telur, sayur",
            "Nasi, ayam, sayur, buah",
            "Nasi, tempe, sayur, susu",
            "Nasi, ikan, sayur, buah",
        ][idx % 4],
        "delivery_timestamp": _ts(2 + (idx % 4), 10 + (idx % 3), 35),
        "expected_timestamp": _ts(2 + (idx % 4), 9, 30),
        "portion_count": vendor["daily_meal_volume"] // max(1, len(vendor["assigned_schools"])),
        "photo_evidence_count": 3,
        "document_complete": idx not in {2, 6, 9},
        "photo_verification": ["Match", "Needs Verification", "Duplicate Suspected", "Menu Mismatch"][idx % 4],
        "verification_status": ["Verified", "Needs Verification", "Flagged", "Under Review"][idx % 4],
        "duplicate_indicator": idx in {3, 7},
        "mismatch_indicator": idx in {1, 4, 8},
        "nutrition_estimate": {
            "calories": 430 + idx * 18,
            "protein_g": 11 + (idx % 5) * 2,
            "carbs_g": 58 + idx,
            "fat_g": 10 + (idx % 4),
        },
        "cost_estimate": {
            "cost_per_portion": 12800 + idx * 760,
            "standard_budget": 15000,
            "cost_anomaly_flag": idx in {4, 8, 10},
        },
        "recommended_follow_up": vendor["recommended_action"],
    }
    for idx, vendor in enumerate(VENDORS + VENDORS[:2], start=1)
]

EVIDENCE: list[dict[str, Any]] = []
evidence_types = ["photo", "document", "text", "public signal"]
for idx in range(1, 21):
    report = REPORTS[(idx - 1) % len(REPORTS)]
    ev_type = evidence_types[idx % 4]
    EVIDENCE.append(
        {
            "id": idx,
            "case_id": report["case_id"],
            "report_id": report["id"],
            "type": ev_type,
            "title": f"{ev_type.title()} evidence package {idx:02d}",
            "linked_entity": report["report_code"],
            "ocr_result": (
                "Simulated OCR: invoice total and portion count extracted with medium confidence."
                if ev_type == "document"
                else None
            ),
            "image_text_match_score": round(0.42 + ((idx % 9) * 0.06), 2) if ev_type == "photo" else None,
            "duplicate_score": round(0.18 + ((idx % 5) * 0.16), 2) if ev_type == "photo" else None,
            "confidence_score": round(0.54 + ((idx % 8) * 0.05), 2),
            "ai_signal": "AI-assisted pre-verification",
            "reviewer_note": [
                "Menu text and image need human review.",
                "Document fields are readable but total cost needs confirmation.",
                "Public signal linked to same vendor cluster.",
                "No sensitive personal data stored in demo evidence.",
            ][idx % 4],
            "created_at": _ts(1 + (idx % 5), 8 + (idx % 9), 5),
        }
    )


def _score_for_report(report: dict[str, Any], idx: int) -> dict[str, Any]:
    vendor = _vendor_lookup[report["vendor_id"]]
    nutrition = 35 + ((idx * 11) % 60)
    cost = 20 + ((idx * 13) % 70)
    anomaly = 15 + ((idx * 17) % 80)
    severity = min(100, int(vendor["risk_score"] * 0.72 + nutrition * 0.18 + anomaly * 0.1))
    confidence = max(40, report["completeness_score"] - (15 if idx in {3, 7} else 0))
    final = min(100, int(severity * 0.42 + confidence * 0.2 + nutrition * 0.16 + cost * 0.12 + anomaly * 0.1))
    label = "Critical" if final >= 80 else "High" if final >= 65 else "Medium" if final >= 45 else "Low"
    explanation = (
        f"{label} priority because {vendor['name']} combines vendor risk {vendor['risk_score']}, "
        f"report completeness {report['completeness_score']}, nutrition concern {nutrition}, "
        f"cost anomaly {cost}, and public-signal anomaly {anomaly}."
    )
    return {
        "id": idx,
        "case_id": report["case_id"],
        "report_id": report["id"],
        "vendor_id": vendor["id"],
        "vendor_name": vendor["name"],
        "region": vendor["region"],
        "severity_score": severity,
        "confidence_score": confidence,
        "nutrition_concern_score": nutrition,
        "cost_anomaly_score": cost,
        "anomaly_score": anomaly,
        "final_priority_score": final,
        "priority_label": label,
        "explanation": explanation + " Operator validation is required before escalation.",
        "recommended_action": vendor["recommended_action"],
        "computed_at": _ts(4, 13, idx),
        "ai_notice": DEMO_NOTICE,
    }


SCORES = [_score_for_report(report, idx) for idx, report in enumerate(REPORTS, start=1)]
SCORES.sort(key=lambda score: score["final_priority_score"], reverse=True)

TICKETS: list[dict[str, Any]] = [
    {
        "id": f"tkt-{idx:03d}",
        "case_id": score["case_id"],
        "title": f"{score['priority_label']} review: {score['vendor_name']}",
        "status": ["Open", "Escalated", "Under Review", "Awaiting Evidence", "Resolved"][idx % 5],
        "sla": "24h" if score["priority_label"] in {"Critical", "High"} else "72h",
        "assigned_unit": [
            "District Food Safety Desk",
            "MBG Vendor Supervision Unit",
            "Nutrition Compliance Team",
            "Procurement Review Desk",
        ][idx % 4],
        "escalation_level": score["priority_label"],
        "linked_vendor_id": score["vendor_id"],
        "linked_vendor_name": score["vendor_name"],
        "linked_region": score["region"],
        "priority": score["final_priority_score"],
        "recommended_action": score["recommended_action"],
        "linked_evidence_ids": [idx, idx + 10 if idx + 10 <= 20 else idx],
        "audit_preview": "Ticket created from evidence fusion and queued for human review.",
        "created_at": _ts(4, 14, idx),
        "updated_at": _ts(4, 15, idx),
    }
    for idx, score in enumerate(SCORES[:10], start=1)
]

AUDIT_TRAIL: list[dict[str, Any]] = []
for idx in range(1, 21):
    ticket = TICKETS[(idx - 1) % len(TICKETS)]
    AUDIT_TRAIL.append(
        {
            "id": idx,
            "case_id": ticket["case_id"],
            "ticket_id": ticket["id"],
            "event_type": [
                "ticket_created",
                "evidence_reviewed",
                "scoring_recomputed",
                "copilot_summary_generated",
                "status_changed",
                "operator_comment_added",
                "escalation_triggered",
            ][idx % 7],
            "actor": ["Demo AI Service", "Operator Dewi", "Supervisor Bima", "System Scheduler"][idx % 4],
            "role": ["AI Assistant", "District Operator", "Supervisor", "System"][idx % 4],
            "description": (
                f"Fictional audit event for {ticket['title']}. Human-in-the-loop review remains required."
            ),
            "timestamp": _ts(4, 8 + (idx % 10), idx % 60),
        }
    )

REGIONAL_HEATMAP = [
    {
        "region": vendor["region"],
        "district": vendor["district"],
        "risk_score": vendor["risk_score"],
        "complaint_count": len([c for c in COMPLAINTS if c["vendor_id"] == vendor["id"]]),
        "high_priority_cases": len([s for s in SCORES if s["vendor_id"] == vendor["id"] and s["final_priority_score"] >= 65]),
        "latitude": [-6.2088, -6.9175, -6.9667, -7.2575, 3.5952, -5.1477, -8.6705, -7.7956][idx],
        "longitude": [106.8456, 107.6191, 110.4167, 112.7521, 98.6722, 119.4327, 115.2126, 110.3695][idx],
    }
    for idx, vendor in enumerate(VENDORS)
]

TRENDS = [
    {"date": f"2026-05-{25 + idx:02d}", "complaints": 12 + idx * 3, "high_priority": 2 + idx % 4, "avg_score": 52 + idx * 4}
    for idx in range(8)
]

ANOMALIES = [
    {
        "id": "ano-001",
        "region": "DKI Jakarta",
        "issue_category": "low protein portion",
        "description": "Complaint volume rose 2.8x over seven-day baseline.",
        "severity": "High",
        "linked_vendor_id": "vnd-001",
    },
    {
        "id": "ano-002",
        "region": "Jawa Barat",
        "issue_category": "suspected food poisoning",
        "description": "Two schools reported similar symptoms within 48 hours.",
        "severity": "Critical",
        "linked_vendor_id": "vnd-002",
    },
    {
        "id": "ano-003",
        "region": "Jawa Timur",
        "issue_category": "cost anomaly",
        "description": "Cost per portion exceeds benchmark while menu completeness declined.",
        "severity": "High",
        "linked_vendor_id": "vnd-004",
    },
]


def overview() -> dict[str, Any]:
    high_risk = len([s for s in SCORES if s["final_priority_score"] >= 65])
    open_tickets = len([t for t in TICKETS if t["status"] != "Resolved"])
    return {
        "total_reports": len(REPORTS) + len(DAILY_REPORTS),
        "public_signals": len(COMPLAINTS),
        "high_risk_cases": high_risk,
        "average_triage_time": "18h",
        "ticket_response_rate": 86,
        "public_signal_spike": "+31%",
        "open_tickets": open_tickets,
        "vendors_on_watchlist": len([v for v in VENDORS if v["watchlist_status"] in {"Critical", "High"}]),
        "ai_notice": DEMO_NOTICE,
        "top_region": max(REGIONAL_HEATMAP, key=lambda item: item["risk_score"])["region"],
    }


def list_response(items: list[dict[str, Any]], page: int = 1, size: int = 50) -> dict[str, Any]:
    start = (page - 1) * size
    end = start + size
    return {"items": items[start:end], "total": len(items), "page": page, "size": size}


def get_or_404(items: list[dict[str, Any]], item_id: str | int, label: str = "Item") -> dict[str, Any]:
    needle = str(item_id)
    for item in items:
        if str(item.get("id")) == needle:
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} '{item_id}' not found")


def vendor_profile(vendor_id: str) -> dict[str, Any]:
    vendor = get_or_404(VENDORS, vendor_id, "Vendor")
    return {
        **vendor,
        "cases": [case for case in oversight_cases() if case["vendor_id"] == vendor_id],
        "linked_complaints": [c for c in COMPLAINTS if c["vendor_id"] == vendor_id],
        "linked_reports": [r for r in REPORTS if r["vendor_id"] == vendor_id],
        "linked_daily_reports": [d for d in DAILY_REPORTS if d["vendor_id"] == vendor_id],
        "ticket_history": [t for t in TICKETS if t["linked_vendor_id"] == vendor_id],
        "nutrition_cost_anomalies": [d for d in DAILY_REPORTS if d["vendor_id"] == vendor_id],
        "audit_notes": [a for a in AUDIT_TRAIL if any(t["case_id"] == a["case_id"] for t in TICKETS if t["linked_vendor_id"] == vendor_id)],
        "ai_notice": DEMO_NOTICE,
    }


def _case_status(ticket: dict[str, Any] | None, report: dict[str, Any] | None) -> str:
    if ticket:
        status_map = {
            "Open": "New",
            "Awaiting Evidence": "Needs Verification",
            "Escalated": "Escalated",
            "Under Review": "Under Review",
            "Resolved": "Resolved",
        }
        return status_map.get(ticket["status"], ticket["status"])
    return report["status"] if report else "Under Review"


def _case_issue(case_id: str, score: dict[str, Any]) -> str:
    complaint = next((item for item in COMPLAINTS if item["case_id"] == case_id), None)
    vendor = _vendor_lookup[score["vendor_id"]]
    return complaint["issue_category"] if complaint else (vendor["repeated_issue_categories"][0] if vendor["repeated_issue_categories"] else "routine monitoring")


def _build_case(score: dict[str, Any]) -> dict[str, Any]:
    case_id = score["case_id"]
    vendor = _vendor_lookup[score["vendor_id"]]
    complaints = [item for item in COMPLAINTS if item["case_id"] == case_id]
    reports = [item for item in REPORTS if item["case_id"] == case_id]
    daily_reports = [item for item in DAILY_REPORTS if item["case_id"] == case_id]
    evidence = [item for item in EVIDENCE if item["case_id"] == case_id]
    ticket = next((item for item in TICKETS if item["case_id"] == case_id), None)
    audit_events = [item for item in AUDIT_TRAIL if item["case_id"] == case_id]
    report = reports[0] if reports else None
    daily = daily_reports[0] if daily_reports else None
    school = (report or daily or {"school": vendor["assigned_schools"][0]})["school"]
    issue = _case_issue(case_id, score)
    signals_count = len(complaints) + len(reports) + len(daily_reports)
    evidence_count = len(evidence)
    title = f"{issue.title()} investigation at {school}"
    what_happened = (
        f"MonitorMBG grouped {signals_count} intake signals for {vendor['name']} into {case_id}. "
        f"The package combines public complaints, official report data, daily vendor evidence, and scoring signals."
    )
    why_it_matters = (
        f"The case affects {school} in {vendor['district']}, {vendor['region']} and may indicate "
        f"{issue} linked to a vendor with risk score {vendor['risk_score']}."
    )
    return {
        "id": case_id,
        "case_id": case_id,
        "title": title,
        "priority_label": score["priority_label"],
        "status": _case_status(ticket, report),
        "vendor_id": vendor["id"],
        "vendor_name": vendor["name"],
        "region": vendor["region"],
        "district": vendor["district"],
        "school": school,
        "issue_category": issue,
        "sla_status": f"{ticket['sla']} SLA" if ticket else "72h SLA",
        "assigned_unit": ticket["assigned_unit"] if ticket else "MBG Vendor Supervision Unit",
        "recommended_action": score["recommended_action"],
        "summary": what_happened,
        "what_happened": what_happened,
        "why_it_matters": why_it_matters,
        "risk_explanation": score["explanation"],
        "signals_count": signals_count,
        "evidence_count": evidence_count,
        "ticket_id": ticket["id"] if ticket else None,
        "created_at": (report or daily or score)["submitted_at"] if report else (daily["delivery_timestamp"] if daily else score["computed_at"]),
        "updated_at": ticket["updated_at"] if ticket else score["computed_at"],
        "vendor": vendor,
        "complaints": complaints,
        "reports": reports,
        "daily_reports": daily_reports,
        "evidence": evidence,
        "score": score,
        "ticket": ticket,
        "copilot_sources": [
            {"label": "Case", "source_type": "case", "source_id": case_id, "title": title},
            {"label": "Vendor", "source_type": "vendor", "source_id": vendor["id"], "title": vendor["name"]},
            {"label": "Score", "source_type": "score", "source_id": score["id"], "title": f"{case_id} score"},
        ],
        "audit_events": audit_events,
        "ai_notice": DEMO_NOTICE,
    }


def oversight_cases() -> list[dict[str, Any]]:
    cases = [_build_case(score) for score in SCORES]
    return sorted(cases, key=lambda item: item["score"]["final_priority_score"], reverse=True)


def case_detail(case_id: str) -> dict[str, Any]:
    for case in oversight_cases():
        if case["case_id"] == case_id or case["id"] == case_id:
            return case
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found")


def copilot_answer(message: str, conversation_id: str | None = None) -> dict[str, Any]:
    query = message.lower()
    top_scores = sorted(SCORES, key=lambda item: item["final_priority_score"], reverse=True)[:3]
    top_vendor = max(VENDORS, key=lambda vendor: vendor["risk_score"])
    sources: list[dict[str, Any]] = []

    if "nutrition" in query or "gizi" in query or "protein" in query:
        related = [s for s in SCORES if s["nutrition_concern_score"] >= 70][:3]
        answer = (
            "Nutrition-related anomalies are concentrated in high-risk cases where protein estimates are low, "
            "menu evidence is incomplete, or fruit/milk is missing. The strongest demo signal is "
            f"{related[0]['vendor_name'] if related else top_scores[0]['vendor_name']} with operator review required."
        )
        sources = _score_sources(related or top_scores)
    elif "region" in query or "wilayah" in query:
        region = max(REGIONAL_HEATMAP, key=lambda item: item["risk_score"])
        answer = (
            f"{region['region']} has the highest regional demo risk score ({region['risk_score']}) "
            f"with {region['complaint_count']} complaint signals and {region['high_priority_cases']} high-priority cases."
        )
        sources = [{"title": "Regional Heatmap", "source_type": "analytics", "source_id": region["region"], "relevance_score": 0.92}]
    elif "evidence" in query or "bukti" in query:
        sample = EVIDENCE[:4]
        answer = (
            "The evidence package combines photo, document, text, and public-signal records. "
            "Simulated OCR, image-text match, duplicate indicators, and reviewer notes should be checked before action."
        )
        sources = [{"title": e["title"], "source_type": "evidence", "source_id": e["id"], "relevance_score": e["confidence_score"]} for e in sample]
    elif "operator" in query or "next" in query or "do next" in query or "tindak" in query:
        answer = (
            "Recommended next step: prioritize Critical and High tickets, request missing evidence for flagged reports, "
            "assign field verification to the relevant district unit, and document every status change in the audit trail."
        )
        sources = _ticket_sources(TICKETS[:3])
    elif "vendor" in query or "watchlist" in query:
        answer = (
            f"{top_vendor['name']} is the highest-risk demo vendor because its risk score is {top_vendor['risk_score']}, "
            f"with repeated issues: {', '.join(top_vendor['repeated_issue_categories'])}. "
            f"Recommended action: {top_vendor['recommended_action']}"
        )
        sources = [{"title": top_vendor["name"], "source_type": "vendor", "source_id": top_vendor["id"], "relevance_score": 0.95}]
    elif "scoring" in query or "score" in query or "report" in query:
        score = top_scores[0]
        answer = (
            f"Top scoring result: {score['case_id']} for {score['vendor_name']} has final priority "
            f"{score['final_priority_score']} ({score['priority_label']}). {score['explanation']}"
        )
        sources = _score_sources([score])
    else:
        answer = (
            "Highest-priority demo cases are "
            + ", ".join(f"{s['case_id']} ({s['vendor_name']}, {s['final_priority_score']})" for s in top_scores)
            + ". These are AI-assisted synthesis outputs and require operator review."
        )
        sources = _score_sources(top_scores)

    return {
        "answer": f"{answer}\n\n{DEMO_NOTICE}",
        "sources": sources,
        "confidence": 0.82,
        "conversation_id": conversation_id or "demo-conversation",
    }


def _score_sources(scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "title": f"{score['case_id']} scoring result",
            "content_snippet": score["explanation"][:180],
            "source_type": "score",
            "source_id": score["id"],
            "relevance_score": round(score["final_priority_score"] / 100, 2),
        }
        for score in scores
    ]


def _ticket_sources(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "title": ticket["title"],
            "content_snippet": ticket["recommended_action"],
            "source_type": "ticket",
            "source_id": ticket["id"],
            "relevance_score": round(ticket["priority"] / 100, 2),
        }
        for ticket in tickets
    ]
