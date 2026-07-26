# MonitorMBG

**AI Oversight Intelligence & Case Orchestration Platform for MBG Vendor Supervision**

MonitorMBG is a GovTech hackathon MVP for **DIGDAYA X HACKATHON 2026**. It is designed as an intelligent oversight layer that complements existing MBG supervision systems. It does **not** replace formal audits, field inspections, or final government decisions.

The current prototype uses fictional, privacy-safe Indonesian demo data and deterministic simulated intelligence outputs so the product can run locally without paid APIs or heavy ML model downloads.

## Product Workflow

MonitorMBG is organized around one operational workflow:

```text
Monitor -> Intake -> Case Creation & Monitoring -> Evidence Review -> Risk Scoring -> Direct Handling or Child Workstreams -> Audit Trail -> Vendor Risk Learning
```

Public signals, official reports, and daily vendor reports enter the Signal Inbox. Related signals are grouped into oversight cases. Each case connects evidence, nutrition/cost checks, scoring, ticketing, copilot synthesis, and audit trail. Vendor profiles accumulate historical risk patterns. Operators use the system for pre-verification and prioritization, while final decisions remain human-led.

Core product story:

```text
Signal -> Case (Open & Monitored) -> Evidence -> Score -> Direct Handling or Optional Child Tickets -> Verified Resolution -> Audit -> Vendor Learning
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
- Oversight Flow Simulator that walks through report intake, AI-assisted pre-verification, evidence fusion, risk scoring, case creation, ticket orchestration, human review, audit trail, Command Center update, and vendor risk learning.
- Signal Inbox that unifies public complaints, official reports, and daily vendor reports.
- Case Work Queue with filters, SLA indicators, recommended actions, and direct case links.
- Case Detail / Investigation Hub as the main handling workspace: case lifecycle, ownership, progress, blockers, evidence, scoring, optional child workstreams, and audit trail.
- Ticket Queue as an optional child-workstream execution layer for linked cases; ticket status does not close a case automatically.
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
- No production-grade migration/rollback policy yet (schema is additive-only so far).
- No production audit/legal workflow.

## Architecture

```text
Next.js Dashboard (3000)
  -> typed API client
  -> FastAPI Backend (8000)
     -> deterministic demo data service
     -> simulated intelligence/scoring helpers
     -> optional Celery/Redis scaffold
     -> PostgreSQL (write-through persistence, SQLAlchemy + Alembic)
```

Read paths serve dict-shaped domain objects loaded from PostgreSQL at startup; every operator mutation is written back through `app/persistence.py`, so runtime state survives restarts. Redis and Celery scaffolds remain in place for the next production phase.

## UX Structure

The navigation is grouped around the oversight workflow:

- Monitoring: Command Center, Oversight Flow Simulator
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
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Persistensi: buat skema lalu muat data demo (sekali saja).
alembic upgrade head
python -m app.dbctl seed --scenario belatung

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Use the Python 3.12 interpreter available on your system. On some machines this may be `python3`, `python3.12`, or a pyenv-managed interpreter.

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

## Database & Seed Workflow

Perubahan operator (kasus baru dari fusion, status tiket, tautan sinyal/bukti,
kepemilikan, jejak audit) **disimpan ke PostgreSQL dan bertahan setelah restart**.
Saat startup backend memuat state dari DB; bila DB tidak tersedia atau belum
di-seed, aplikasi otomatis kembali ke data demo in-memory (demo tetap jalan).

Semua perintah dijalankan dari `backend/` dengan virtualenv aktif.

```bash
alembic upgrade head                        # buat/perbarui skema
python -m app.dbctl seed                    # baseline demo (MBG-001..010)
python -m app.dbctl seed --scenario belatung  # baseline + skenario kontaminasi
python -m app.dbctl reset                   # kembali ke baseline (buang data runtime)
python -m app.dbctl reset --scenario belatung
python -m app.dbctl reset --empty           # kosongkan DB, tanpa seed
python -m app.dbctl status                  # jumlah baris + pembagian seed/runtime
```

Mode pengembangan:

| Mode | Perintah | Kegunaan |
| --- | --- | --- |
| Baseline demo | `dbctl seed` | Demo standar, data selalu sama |
| Baseline + skenario | `dbctl seed --scenario belatung` | Latihan alur evidence fusion |
| Kosong | `dbctl reset --empty` | Uji alur dari nol tanpa data bawaan |
| Live persistent | jalankan backend seperti biasa | Perubahan operator terakumulasi lintas restart |

Baris seed ditandai `is_seeded=True` beserta `seed_group` (`baseline`,
`belatung`), sedangkan baris hasil aksi operator bernilai `is_seeded=False`.
`dbctl status` menampilkan pemisahan itu. `reset` bersifat menyeluruh: baris
runtime mereferensikan baris seed (bukti hasil fusion menunjuk sinyal seed),
sehingga satu lapis tidak dapat dihapus sendiri tanpa melanggar foreign key.

Skenario `belatung` memuat sinyal #19 (laporan pengawas, lampiran `4.jpg`) dan
#20 (unggahan media sosial, lampiran `26.jpg`) dalam status belum dibentuk
kasus, siap dipakai untuk mendemokan penggabungan sinyal menjadi satu kasus.

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

## End-to-End Demo Flow

```text
Oversight Flow Simulator
-> Submit Demo Report
-> AI-Assisted Pre-Verification
-> Evidence Fusion
-> Risk Scoring
-> Case Creation
-> Ticket Orchestration
-> Human Review
-> Audit Trail
-> Command Center Update
-> Vendor Risk Learning
```

## Recommended Judge Demo

```text
1. Open /simulation
2. Run the golden scenario
3. Open generated case detail
4. Review evidence and scoring
5. Ask Copilot
6. Update ticket through human review
7. Open audit trail
8. Open vendor profile
9. Return to Command Center
```

## Recommended Demo Flow

```text
Oversight Flow Simulator -> Case Detail -> Signals -> Evidence -> Scoring -> Copilot -> Ticket -> Audit Trail -> Vendor Profile -> Command Center
```

1. Start at `/simulation` and run the Low Protein Portion + Late Delivery Pattern scenario.
2. Open the generated `case-001` detail page.
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

## Honest AI Note

The MVP uses deterministic demo intelligence to simulate AI-assisted pre-verification, evidence fusion, scoring, and bounded copilot behavior. Production deployment would replace or augment these modules with validated models, secure integrations, model monitoring, and government-approved data pipelines.

## Responsive QA Checklist

Before a judge demo, check the app at 320, 375, 768, 1024, and 1440 px widths. Also check browser zoom at 125% and 150%.

Priority routes:

- `/simulation`
- `/cases/case-001`
- `/`
- `/intake`
- `/tickets`
- `/vendors/vnd-001`
- `/audit-trail`
- `/copilot`

Responsive review points:

- No page-level horizontal scroll except inside table/tab scroll containers.
- Long vendor, school, issue, status, and action text wraps without breaking card layouts.
- Tabs remain usable on small screens.
- Score cards, metric cards, ticket actions, and timeline rows stack cleanly.
- Copilot chat messages and source cards remain readable on mobile.

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

- Seed data is deterministic; run `alembic upgrade head` + `python -m app.dbctl seed` once to enable persistence.
- Without a reachable database the app falls back to in-memory demo data and runtime changes are lost on restart.
- Reports/daily reports remain derived projections over cases (no tables of their own).
- Celery tasks are scaffolded but not required for the current demo.
- Real model inference is intentionally excluded from default setup.

## Next Development Phase

- Move read paths onto async ORM queries so the process holds no shared mutable state.
- Add authentication, RBAC, and operator identity.
- Add vendor licensing/perizinan workflows.
- Add production evidence storage and chain-of-custody controls.
- Integrate evaluated NLP/CV/OCR models behind clearly governed interfaces.
- Add real Satu Data-compatible integration contracts.
- Expand tests and CI/CD.
