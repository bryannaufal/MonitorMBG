"""Muat data kanonik (``seed_data``) ke PostgreSQL.

Jalankan dari keadaan DB kosong SETELAH migration:
    python -m app.seed

Idempoten: mengosongkan tabel pengawasan lalu memuat ulang. Sumbernya sama
persis dengan yang dipakai API demo & fallback frontend — tidak ada divergensi.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from sqlalchemy import delete

from app import seed_data as sd
from app.core.database import async_session_factory
from app.models.oversight import (
    AuditEvent,
    Case,
    Evidence,
    RiskAssessment,
    Signal,
    Ticket,
    Vendor,
    VerificationReview,
)


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


async def seed() -> None:
    async with async_session_factory() as session:
        # Kosongkan (urutan aman terhadap foreign key).
        for model in (AuditEvent, VerificationReview, Ticket, RiskAssessment, Evidence, Signal, Case, Vendor):
            await session.execute(delete(model))

        for v in sd.VENDORS:
            session.add(Vendor(**v))
        await session.flush()

        for c in sd.CASES:
            session.add(Case(
                case_id=c["case_id"], vendor_id=c["vendor_id"], school=c["school"],
                issue_category=c["issue_category"], priority_label=c["priority_label"],
                status=c["status"], title=c["title"],
                created_at=_dt(c["created_at"]), updated_at=_dt(c["updated_at"]),
            ))
        await session.flush()

        for s in sd.SIGNALS:
            session.add(Signal(
                id=s["id"], case_id=s.get("case_id"), source=s["source"],
                source_confidence=s["source_confidence"], urgency=s["urgency"], status=s["status"],
                summary=s["summary"], text=s["text"], vendor_id=s.get("vendor_id"),
                vendor_name=s.get("vendor_name", ""), region=s.get("region", ""),
                district=s.get("district", ""), school=s.get("school", ""),
                issue_category=s.get("issue_category", ""), created_at=_dt(s["created_at"]),
            ))
        await session.flush()

        for e in sd.EVIDENCE:
            session.add(Evidence(
                id=e["id"], case_id=e["case_id"], signal_id=e.get("signal_id"), type=e["type"],
                title=e["title"], file_path=e["file_path"], linked_entity=e["linked_entity"],
                source=e["source"], ocr_result=e.get("ocr_result"),
                image_text_match_score=e.get("image_text_match_score"),
                duplicate_score=e.get("duplicate_score"), confidence_score=e["confidence_score"],
                review_status=e["review_status"], reviewer_note=e["reviewer_note"],
                created_at=_dt(e["created_at"]),
            ))
            # Satu tinjauan verifikasi awal per bukti (status pra-verifikasi).
            session.add(VerificationReview(
                evidence_id=e["id"], case_id=e["case_id"], reviewer="Operator Dewi",
                result=e["review_status"], note="Tinjauan awal pra-verifikasi; keputusan akhir oleh operator.",
                reviewed_at=_dt(e["created_at"]),
            ))
        await session.flush()

        for r in sd.RISK:
            session.add(RiskAssessment(
                id=r["id"], case_id=r["case_id"], vendor_id=r["vendor_id"], vendor_name=r["vendor_name"],
                region=r["region"], severity_score=r["severity_score"], confidence_score=r["confidence_score"],
                nutrition_concern_score=r.get("actionability_score", 0),
                cost_anomaly_score=0,
                anomaly_score=0,
                final_priority_score=r["final_priority_score"],
                priority_label=r["priority_label"], explanation=r["explanation"],
                recommended_action=r["recommended_action"], computed_at=_dt(r["computed_at"]),
            ))

        for t in sd.TICKETS:
            session.add(Ticket(
                id=t["id"], case_id=t["case_id"], title=t["title"], status=t["status"], sla=t["sla"],
                assigned_unit=t["assigned_unit"], escalation_level=t["escalation_level"],
                linked_vendor_id=t["linked_vendor_id"], linked_vendor_name=t["linked_vendor_name"],
                linked_region=t["linked_region"], priority=t["priority"],
                recommended_action=t["recommended_action"], linked_evidence_ids=t["linked_evidence_ids"],
                audit_preview=t["audit_preview"], created_at=_dt(t["created_at"]), updated_at=_dt(t["updated_at"]),
            ))

        for a in sd.AUDIT:
            session.add(AuditEvent(
                id=a["id"], case_id=a["case_id"], ticket_id=a.get("ticket_id"), event_type=a["event_type"],
                actor=a["actor"], role=a["role"], description=a["description"], timestamp=_dt(a["timestamp"]),
            ))

        await session.commit()
    print(f"✓ Seed selesai: {len(sd.VENDORS)} vendor, {len(sd.CASES)} kasus, "
          f"{len(sd.SIGNALS)} sinyal, {len(sd.EVIDENCE)} bukti, {len(sd.TICKETS)} tiket.")


if __name__ == "__main__":
    asyncio.run(seed())
