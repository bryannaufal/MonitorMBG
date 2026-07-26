"""Model ORM pengawasan MonitorMBG (relasi kanonik prototype).

Relasi:
- vendor 1—* case
- case 1—* signal (signal juga bisa tanpa case: belum dibentuk kasus)
- case 1—* evidence (evidence punya file_path foto lokal)
- case 1—1 risk_assessment aktif
- case 1—* ticket (optional child workstreams)
- evidence 1—* verification_review
- semua perubahan penting -> audit_event
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SeedProvenance:
    """Marks whether a row came from a seed load or from operator runtime action.

    ``reset --to-baseline`` deletes runtime rows and reloads seeds; ``seed_group``
    names which loader wrote the row (``baseline``, ``belatung``, ...) so a single
    scenario can be dropped without touching the rest.
    """

    is_seeded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    seed_group: Mapped[str | None] = mapped_column(String, nullable=True)


class Vendor(SeedProvenance, Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    region: Mapped[str] = mapped_column(String, nullable=False)
    district: Mapped[str] = mapped_column(String, nullable=False)
    assigned_schools: Mapped[list] = mapped_column(JSON, default=list)
    daily_meal_volume: Mapped[int] = mapped_column(Integer, default=0)
    compliance_status: Mapped[str] = mapped_column(String, default="")
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_trend: Mapped[list] = mapped_column(JSON, default=list)
    watchlist_status: Mapped[str] = mapped_column(String, default="")
    watchlist_reason: Mapped[str] = mapped_column(Text, default="")
    last_inspection_date: Mapped[str] = mapped_column(String, default="")
    repeated_issue_categories: Mapped[list] = mapped_column(JSON, default=list)
    coverage_notes: Mapped[str] = mapped_column(Text, default="")
    recommended_action: Mapped[str] = mapped_column(Text, default="")

    cases: Mapped[list["Case"]] = relationship(back_populates="vendor")


class Case(SeedProvenance, Base):
    __tablename__ = "cases"

    case_id: Mapped[str] = mapped_column(String, primary_key=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), nullable=False)
    school: Mapped[str] = mapped_column(String, nullable=False)
    region: Mapped[str | None] = mapped_column(String, nullable=True)
    district: Mapped[str | None] = mapped_column(String, nullable=True)
    vendor_name_override: Mapped[str | None] = mapped_column(String, nullable=True)
    vendor_source_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_investigator: Mapped[str | None] = mapped_column(String, nullable=True)
    assigned_unit: Mapped[str | None] = mapped_column(String, nullable=True)
    severity: Mapped[str | None] = mapped_column(String, nullable=True)
    issue_category: Mapped[str] = mapped_column(String, nullable=False)
    priority_label: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    case_type: Mapped[str | None] = mapped_column(String, nullable=True)
    case_subtype: Mapped[str | None] = mapped_column(String, nullable=True)
    impact_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_owner: Mapped[str | None] = mapped_column(String, nullable=True)
    handling_team: Mapped[str | None] = mapped_column(String, nullable=True)
    secondary_owner: Mapped[str | None] = mapped_column(String, nullable=True)
    watchers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    handling_strategy: Mapped[str | None] = mapped_column(String, nullable=True)
    related_case_id: Mapped[str | None] = mapped_column(String, nullable=True)
    case_relationship: Mapped[str | None] = mapped_column(String, nullable=True)
    blockers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    resolution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    vendor: Mapped["Vendor"] = relationship(back_populates="cases")
    signals: Mapped[list["Signal"]] = relationship(back_populates="case")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="case")
    risk: Mapped["RiskAssessment"] = relationship(back_populates="case", uselist=False)
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="case")


class Signal(SeedProvenance, Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str | None] = mapped_column(ForeignKey("cases.case_id"), nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    source_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    urgency: Mapped[str] = mapped_column(String, default="Sedang")
    status: Mapped[str] = mapped_column(String, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    text: Mapped[str] = mapped_column(Text, default="")
    vendor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    vendor_name: Mapped[str] = mapped_column(String, default="")
    region: Mapped[str] = mapped_column(String, default="")
    district: Mapped[str] = mapped_column(String, default="")
    school: Mapped[str] = mapped_column(String, default="")
    issue_category: Mapped[str] = mapped_column(String, default="")
    attachment_path: Mapped[str | None] = mapped_column(String, nullable=True)
    attachment_title: Mapped[str | None] = mapped_column(String, nullable=True)
    attachment_source: Mapped[str | None] = mapped_column(String, nullable=True)
    attachment_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    case: Mapped["Case | None"] = relationship(back_populates="signals")


class Evidence(SeedProvenance, Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    signal_id: Mapped[int | None] = mapped_column(ForeignKey("signals.id"), nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(String, default="")
    linked_entity: Mapped[str] = mapped_column(String, default="")
    source: Mapped[str] = mapped_column(String, default="")
    ocr_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_text_match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    duplicate_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    review_status: Mapped[str] = mapped_column(String, default="Perlu Ditinjau")
    reviewer_note: Mapped[str] = mapped_column(Text, default="")
    unlinked_from_case: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    case: Mapped["Case"] = relationship(back_populates="evidence")
    reviews: Mapped[list["VerificationReview"]] = relationship(back_populates="evidence")


class VerificationReview(Base):
    __tablename__ = "verification_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("evidence.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    reviewer: Mapped[str] = mapped_column(String, default="")
    result: Mapped[str] = mapped_column(String, default="Perlu Ditinjau")
    note: Mapped[str] = mapped_column(Text, default="")
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    evidence: Mapped["Evidence"] = relationship(back_populates="reviews")


class RiskAssessment(SeedProvenance, Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    vendor_id: Mapped[str] = mapped_column(String, nullable=False)
    vendor_name: Mapped[str] = mapped_column(String, default="")
    region: Mapped[str] = mapped_column(String, default="")
    severity_score: Mapped[int] = mapped_column(Integer, default=0)
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    nutrition_concern_score: Mapped[int] = mapped_column(Integer, default=0)
    cost_anomaly_score: Mapped[int] = mapped_column(Integer, default=0)
    anomaly_score: Mapped[int] = mapped_column(Integer, default=0)
    final_priority_score: Mapped[int] = mapped_column(Integer, default=0)
    priority_label: Mapped[str] = mapped_column(String, default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    recommended_action: Mapped[str] = mapped_column(Text, default="")
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    case: Mapped["Case"] = relationship(back_populates="risk")


class Ticket(SeedProvenance, Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    # Not unique: a case owns many child workstreams.  The old UNIQUE
    # constraint was dropped in migration 9c3f2ab7c1d0 but lingered here, so a
    # freshly created schema still rejected the second ticket on a case.
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str | None] = mapped_column(String, nullable=True)
    impact: Mapped[str | None] = mapped_column(String, nullable=True)
    urgency: Mapped[str | None] = mapped_column(String, nullable=True)
    sla_policy: Mapped[str | None] = mapped_column(String, nullable=True)
    sla: Mapped[str] = mapped_column(String, default="")
    assignee: Mapped[str | None] = mapped_column(String, nullable=True)
    assignment_group: Mapped[str | None] = mapped_column(String, nullable=True)
    assigned_unit: Mapped[str] = mapped_column(String, default="")
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    labels: Mapped[list | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    escalation_level: Mapped[str] = mapped_column(String, default="")
    linked_vendor_id: Mapped[str] = mapped_column(String, default="")
    linked_vendor_name: Mapped[str] = mapped_column(String, default="")
    linked_region: Mapped[str] = mapped_column(String, default="")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    recommended_action: Mapped[str] = mapped_column(Text, default="")
    linked_evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    audit_preview: Mapped[str] = mapped_column(Text, default="")
    workstream: Mapped[str | None] = mapped_column(String, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    case: Mapped["Case"] = relationship(back_populates="tickets")


class AuditEvent(SeedProvenance, Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Nullable: signal review/defer records an event before any case exists.
    case_id: Mapped[str | None] = mapped_column(ForeignKey("cases.case_id"), nullable=True)
    ticket_id: Mapped[str | None] = mapped_column(String, nullable=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    actor: Mapped[str] = mapped_column(String, default="")
    role: Mapped[str] = mapped_column(String, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
