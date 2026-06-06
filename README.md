# MonitorMBG

**AI Oversight Intelligence & Case Orchestration Platform for MBG Vendor Supervision**

MonitorMBG is a GovTech hackathon MVP for **DIGDAYA X HACKATHON 2026**. It is designed as an intelligent oversight layer that complements existing MBG supervision systems. It does **not** replace formal audits, field inspections, or final government decisions.

The current prototype uses fictional, privacy-safe Indonesian demo data and deterministic simulated intelligence outputs so the product can run locally without paid APIs or heavy ML model downloads.

## Product Workflow

MonitorMBG is organized around one operational workflow:

```text
Monitor -> Intake -> Case Creation -> Evidence Review -> Risk Scoring -> Ticket Action -> Audit Trail -> Vendor Risk Learning
```

Public signals, official reports, and daily vendor reports enter the Signal Inbox. Related signals are grouped into oversight cases. Each case connects evidence, nutrition/cost checks, scoring, ticketing, copilot synthesis, and audit trail. Vendor profiles accumulate historical risk patterns. Operators use the system for pre-verification and prioritization, while final decisions remain human-led.

Core product story:

```text
Signal -> Case -> Evidence -> Score -> Ticket -> Audit -> Vendor Learning
```

## Product Positioning

MonitorMBG helps operators supervise MBG vendors/SPPG through:

- public signal intelligence from social/community/school complaint channels,
- assisted official and daily vendor reporting,
- multimodal evidence pre-verification,
- evidence fusion and hybrid risk scoring,
- ticket/case orchestration,
- vendor watchlist and risk profiles,
- bounded AI copilot synthesis,
- audit trail and human-in-the-loop governance.

## MVP Feature List

Implemented demo workflows:

- Command Center dashboard with active cases, critical/high-risk cases, incoming signals, regional risk, anomaly alerts, watchlist preview, and priority work queue.
- Signal Inbox that unifies public complaints, official reports, and daily vendor reports.
- Case Work Queue with filters, SLA indicators, recommended actions, and direct case links.
- Case Detail / Investigation Hub with Overview, Signals, Evidence, Scoring, Ticket, Copilot, and Audit Trail tabs.
- Ticket Queue as the operational action layer for linked cases.
- Risk Prioritization page with explainable final priority scores linked back to cases.
- Nutrition & Cost Intelligence page connected to cases and vendors.
- Regional Risk Intelligence page with ranked regional concentration signals.
- Vendor Watchlist and Vendor Risk Profile pages that show recurring risk patterns.
- Governance Log for AI outputs, operator actions, ticket changes, evidence review, and escalations.
- Bounded AI Case Copilot that answers from internal demo data and cites demo sources.
- FastAPI `/docs` with working `/api/v1` endpoints.

## Prototype Status

Implemented:

- Next.js dashboard and all required pages.
- FastAPI API surface with deterministic demo data.
- Fictional vendors, cases, complaints, reports, daily reports, evidence, scoring, tickets, audit events, analytics.
- First-class case aggregation linking vendor, signals, reports, daily evidence, score, ticket, copilot sources, and audit events.
- Rule-based demo scoring and nutrition/cost plausibility outputs.
- Bounded copilot response synthesis without external API calls.
- Basic backend smoke tests.

Simulated:

- AI classification and case synthesis.
- OCR/document parsing.
- Image-text consistency.
- Duplicate photo detection.
- Nutrition plausibility.
- Public signal anomaly detection.
- Evidence fusion.

Not production-ready:

- No real government data.
- No real social scraping.
- No deployed ML/CV/OCR/RAG models.
- No formal identity provider or full RBAC enforcement.
- No persistent ticket mutation across restarts.
- No production audit/legal workflow.

## Architecture

```text
Next.js Dashboard (3000)
  -> typed API client
  -> FastAPI Backend (8000)
     -> deterministic demo data service
     -> simulated intelligence/scoring helpers
     -> optional Celery/Redis scaffold
     -> optional PostgreSQL scaffold
```

The MVP is intentionally demo-data driven. PostgreSQL, Redis, SQLAlchemy, Alembic, and Celery scaffolds remain in place for the next production phase.

## UX Structure

The navigation is grouped around the oversight workflow:

- Monitoring: Command Center
- Intake: Signal Inbox
- Case Work: Cases, Tickets
- Intelligence: Risk Prioritization, Nutrition & Cost, Regional Heatmap
- Vendor Oversight: Vendor Watchlist
- Governance: Governance Log, AI Case Copilot

## Local Development Setup

Recommended reliable path:

```bash
cd ~/projects/MonitorMBG
docker compose up -d postgres redis

cd backend
/home/mcdimas/.local/bin/python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Use Python 3.12 for the backend. On this machine, plain `python3` points to Python 3.14, which is newer than the pinned FastAPI/Pydantic runtime stack.

In another terminal:

```bash
cd ~/projects/MonitorMBG/frontend
npm install
npm run dev
```

URLs:

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/health
- Backend docs: http://localhost:8000/docs

## Docker Setup

Infrastructure only:

```bash
docker compose up -d postgres redis
```

Full stack:

```bash
cp .env.example .env
docker compose up --build
```

Docker compose overrides backend service hostnames to use `postgres` and `redis`. `.env.example` remains optimized for manual local development from the host.

## Recommended Demo Flow

```text
Command Center -> High-Risk Case -> Signals -> Evidence -> Scoring -> Copilot -> Ticket -> Audit Trail -> Vendor Profile
```

1. Start at Command Center and review what needs attention now.
2. Open a high-risk case from the Priority Work Queue.
3. Review Signals to show how complaints, official reports, and daily reports entered the system.
4. Review Evidence to show OCR, image-text match, duplicate warning, confidence, and reviewer notes.
5. Open Scoring to explain severity, confidence, nutrition, cost, anomaly, and final priority.
6. Open Copilot to synthesize the case with source cards and human review disclaimer.
7. Open Ticket and simulate an operator action such as escalation or field verification.
8. Open Audit Trail to prove traceability.
9. Open Vendor Profile to show whether this is recurring vendor risk.
10. Ask Global AI Case Copilot:
    - “Which cases are highest priority?”
    - “Summarize the highest risk vendor.”
    - “What evidence supports this case?”
    - “Show nutrition-related anomalies.”
    - “Which region has the highest risk?”

## API Overview

Health:

- `GET /health`

Analytics:

- `GET /api/v1/analytics/overview`
- `GET /api/v1/analytics/heatmap`
- `GET /api/v1/analytics/trends`
- `GET /api/v1/analytics/anomalies`

Core data:

- `GET /api/v1/cases`
- `GET /api/v1/cases/{case_id}`
- `GET /api/v1/complaints`
- `GET /api/v1/complaints/{id}`
- `GET /api/v1/reports`
- `GET /api/v1/reports/{id}`
- `GET /api/v1/daily-reports`
- `GET /api/v1/daily-reports/{id}`
- `GET /api/v1/daily-reports/{id}/verification`
- `GET /api/v1/evidence`
- `GET /api/v1/evidence/{id}`
- `GET /api/v1/nutrition/summary`
- `GET /api/v1/nutrition/report/{id}`
- `GET /api/v1/scoring/rankings`
- `GET /api/v1/scoring/report/{id}`
- `POST /api/v1/scoring/recompute/{id}`
- `GET /api/v1/tickets`
- `GET /api/v1/tickets/{id}`
- `PATCH /api/v1/tickets/{id}/status`
- `GET /api/v1/vendors`
- `GET /api/v1/vendors/{id}`
- `GET /api/v1/audit-trail`
- `GET /api/v1/audit-trail/case/{case_id}`
- `POST /api/v1/copilot/chat`
- `POST /api/v1/copilot/chat/stream`

## Safety and Governance Note

AI output is a pre-verification signal. Final decisions remain with authorized operators. The demo uses fictional data, avoids real personal data, and is framed for PDP/SPBE/Satu Data-aligned supervision design discussions.

## Known Limitations

- Data is deterministic and in memory.
- Ticket status updates are not persisted after restart.
- Database migrations are not required for the MVP flow.
- Celery tasks are scaffolded but not required for the current demo.
- Real model inference is intentionally excluded from default setup.

## Next Development Phase

- Add persisted PostgreSQL demo seed and migrations.
- Add authentication, RBAC, and operator identity.
- Add vendor licensing/perizinan workflows.
- Add production evidence storage and chain-of-custody controls.
- Integrate evaluated NLP/CV/OCR models behind clearly governed interfaces.
- Add real Satu Data-compatible integration contracts.
- Expand tests and CI/CD.
