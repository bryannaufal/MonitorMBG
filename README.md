# MonitorMBG

**AI Oversight Intelligence & Case Orchestration Platform for MBG Vendor Supervision**

MonitorMBG is a GovTech hackathon MVP for **DIGDAYA X HACKATHON 2026**. It is an intelligent oversight layer that complements existing MBG supervision systems. It does **not** replace formal audits, field inspections, or final government decisions.

The prototype uses fictional, privacy-safe Indonesian demo data. **Seed workflows run without API keys** (rules + pre-baked assessments). Optional **Kimi** (scoring/vision/chat) and **Gemini** (Copilot embeddings) activate when keys are set in `.env`.

## Product Workflow

```text
Monitor → Intake → Review & Case Creation → Evidence → 4-Factor Scoring → Ticket Action → Audit → Vendor Learning
```

Public signals enter **Kotak Masuk Sinyal** via social/news scrape or operator review. **Lapor MBG** (public form) creates follow-up tickets. Related signals are merged into oversight cases. Each case links evidence, scoring, tickets, Copilot synthesis, and audit events.

```text
Signal → (optional auto-ticket) → Case → Evidence → Score → Ticket → Audit → Vendor profile
```

## Product Positioning

MonitorMBG helps operators supervise MBG vendors/SPPG through:

- **Signal intake** — fixture demo feed, live X (twitterapi.io), or Google News RSS
- **4-factor risk scoring** — Dampak, Keyakinan, Dapat Ditindak, plus separate Gizi estimate
- **Auto-ticket gate** — optional automatic case/ticket when score + risk triggers pass threshold
- **Case review** — merge/create/defer signals with human-in-the-loop
- **Bounded AI Copilot** — in-memory RAG over cases + Kimi synthesis
- **Governance** — audit trail, pre-verification disclaimers, operator override

## Scoring Model (4-Factor)

| Factor | Backend field | In priority formula? | Notes |
|--------|---------------|----------------------|--------|
| **Dampak** | `severity_score` | 50% | Issue impact (safety, contamination, nutrition) |
| **Keyakinan** | `confidence_score` | 25% | Source channel trust (rules) |
| **Dapat Ditindak** | `actionability_score` | 25% | Location, school, attachment completeness |
| **Gizi** | `nutrition_score` | No (informational) | Photo/description estimate; shown separately |

```text
Skor prioritas = min(95, 50%×Dampak + 25%×Keyakinan + 25%×Dapat Ditindak + bonus)
```

**Seed signals (#1–20):** pre-baked assessments in `backend/app/data/signal_assessment_seed.json` — **no Kimi on open**.

**Runtime signals:** Kimi text scoring + optional Kimi vision for Gizi when `SCRAPER_MODE=live` and `KIMI_API_KEY` is set; otherwise rules fallback.

## Intake & Auto-Ticket

| Path | Destination |
|------|----------------|
| Scrape (fixture / X / RSS) | Kotak Masuk Sinyal (runtime signals, id ≥ 9001) |
| Lapor MBG (`/lapor`) | Tiket Tindak Lanjut (+ optional auto-ticket) |
| Review → Bentuk Kasus | Cases + in-memory backend + browser overlay |

**`SCRAPER_MODE`**

- `fixture` — load `backend/app/data/social_feed_fixture.json`; rules-only scoring
- `live` — fetch X and/or Google News RSS; Kimi when key present; falls back to fixture on fetch failure

**`AUTO_TICKET_ON_INTAKE`** (default `false` in `.env.example`)

When `true`, after intake each signal is scored and passed through `auto_ticket_gate`:

- Priority score ≥ **55**
- At least one trigger: Kritis urgency, high-risk category, attachment, or severity ≥ 75
- Social signals with incomplete location need score ≥ **75**

## AI Copilot (Asisten Ringkasan Kasus)

| Layer | Provider | When |
|-------|----------|------|
| **Embeddings / RAG search** | Gemini (`GEMINI_API_KEY`) | Preferred |
| **Embeddings fallback** | Local hash (`local-fixture-v1`) | No Gemini key |
| **Chat synthesis** | Kimi (`KIMI_API_KEY`) | When set |
| **Fallback answer** | RAG snippet or keyword demo | No Kimi / empty RAG |

RAG is **in-memory**. On each chat request the backend syncs all cases in `sd.CASES` and indexes **client overlay cases** sent from the browser (`localStorage`) so runtime cases (e.g. MBG-011) can appear in answers after restart.

Hybrid retrieval: case number match (`MBG-011`), keyword overlap, + semantic similarity.

## MVP Feature List

- Command Center, Oversight Flow Simulator (aligned with 4-factor + Gizi model)
- **Kotak Masuk Sinyal** — seed + runtime signals, scrape job, review workflow
- **Lapor MBG** — public intake form → tickets
- **Cases** — filters, SLA, factor scores, runtime overlay merge
- **Case detail** — signals, evidence, scoring, ticket, copilot sources, audit
- **Tiket Tindak Lanjut** — sort by priority or date
- Risk Prioritization, Gizi & Biaya, Regional Heatmap, Vendor Watchlist
- Governance Log / Jejak Audit
- **Asisten Ringkasan Kasus** — RAG + Kimi
- FastAPI `/docs` — full `/api/v1` surface

## Prototype Status

**Implemented (demo / in-memory):**

- Next.js dashboard and navigation (Indonesian labels)
- FastAPI backend with seed data + **runtime mutation** (cases, signals, tickets per session)
- Unified `risk_scorer`, `nutrition_scorer`, `kimi_signal_scorer`
- Social scraper + public form intake
- Auto-ticket gate + ticket service
- Copilot RAG store, indexer, synthesizer
- Frontend **runtime overlay** (`localStorage`) so operator actions survive page refresh
- Backend tests for scoring, nutrition, copilot RAG, Kimi integration

**Optional with API keys:**

- Kimi — live signal scoring, Gizi vision, Copilot chat
- Gemini — Copilot embedding quality
- twitterapi.io — live X scrape

**Simulated / seed-only:**

- OCR, duplicate photo detection, full CV pipeline (demo labels on evidence)
- Persistent PostgreSQL for MVP flow (scaffold present)

**Not production-ready:**

- No real government or PII data
- Runtime data lost on backend restart (overlay partially restores UI state)
- No formal RBAC / identity provider
- No production model governance or Satu Data integration

## Architecture

```text
Next.js (3000)
  ├─ API client + runtimeOverlay (localStorage)
  └─ FastAPI (8000)
       ├─ seed_data + runtime_store (in-memory)
       ├─ review_store / ticket_service
       ├─ scoring (rules + optional Kimi/vision)
       ├─ intake (scraper, public form)
       ├─ copilot (RAG in-memory + optional Gemini/Kimi)
       └─ optional PostgreSQL, Redis, Celery scaffolds
```

## UX Structure

| Group | Pages |
|-------|--------|
| Pemantauan | Pusat Kendali, Simulator Alur Pengawasan |
| Intake | Kotak Masuk Sinyal, Lapor MBG (Publik) |
| Kerja Kasus | Kasus, Tiket Tindak Lanjut |
| Intelijen | Penilaian Risiko, Gizi & Biaya, Heatmap Wilayah |
| Pengawasan Vendor | Daftar Pantauan Vendor |
| Tata Kelola | Jejak Audit, Asisten Ringkasan Kasus |

## Local Development Setup

### 1. Environment

```bash
cp .env.example .env
# Edit .env — never commit real API keys
```

Minimal demo (no paid APIs):

```env
SCRAPER_MODE=fixture
AUTO_TICKET_ON_INTAKE=false
# Leave KIMI_API_KEY and GEMINI_API_KEY empty
```

### 2. Infrastructure (optional)

```bash
docker compose up -d postgres redis
```

### 3. Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

**URLs**

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

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

Docker Compose overrides `DATABASE_URL` / `REDIS_URL` for container hostnames. `.env.example` targets manual host development.

## Environment Variables (summary)

See [`.env.example`](.env.example) for full comments.

| Variable | Purpose |
|----------|---------|
| `KIMI_API_KEY` | Live scoring, Gizi vision, Copilot chat |
| `GEMINI_API_KEY` | Copilot RAG embeddings (local fallback if empty) |
| `SCRAPER_MODE` | `fixture` \| `live` |
| `SCRAPER_LIVE_PROVIDER` | `twitter`, `rss`, or comma list |
| `TWITTERAPI_IO_API_KEY` | Live X scrape |
| `AUTO_TICKET_ON_INTAKE` | Auto case/ticket after scrape/form when gate passes |
| `NEXT_PUBLIC_API_URL` | Frontend → backend API base |

## Utility Scripts

```bash
# Regenerate seed signal assessments (optional Kimi vision for photos)
cd backend && PYTHONPATH=. python scripts/bake_signal_assessments.py

# Build Copilot RAG fixture JSON from seed cases
cd backend && PYTHONPATH=. python scripts/build_copilot_rag_fixture.py
```

## Recommended Demo Flow

1. **`/simulation`** — run golden scenario (4-factor + Gizi explained)
2. **`/intake`** — scrape (fixture) or review signal #19 (belatung + photo)
3. **`/signals/19/review`** — Bentuk Kasus → new case appears on **`/cases`**
4. **`/cases/case-001`** — evidence, scoring, ticket, audit tabs
5. **`/copilot`** — ask about priority cases or belatung (RAG + Kimi if keys set)
6. **`/lapor`** — submit public report → **`/tickets`**
7. **`/audit-trail`** — traceability

**Copilot sample questions**

- “Kasus mana yang prioritas tertinggi?”
- “Apakah ada case belatung?”
- “Apakah ada MBG-011?” (after creating runtime case; overlay syncs on chat)

## API Overview

**Health:** `GET /health`

**Intake**

- `POST /api/v1/intake/scrape` — start scrape job
- `GET /api/v1/intake/scrape/status`
- `POST /api/v1/intake/form` — Lapor MBG public form

**Signals**

- `GET /api/v1/signals`
- `GET /api/v1/signals/{id}/assessment` — 4-factor pre-assessment
- `POST /api/v1/signals/{id}/review` — merge / create case / defer
- `GET /api/v1/signals/{id}/auto-evaluate`
- `POST /api/v1/signals/{id}/auto-ticket`

**Cases, tickets, scoring, vendors, audit** — see `/docs`

**Copilot**

- `POST /api/v1/copilot/chat` — body: `{ "message", "client_cases"?: [...] }`
- `POST /api/v1/copilot/ingest` — re-index all cases into RAG

## Data & Persistence Notes

| Data | Persistence |
|------|-------------|
| Seed cases/signals (#1–20) | Code + JSON fixtures |
| Runtime cases/signals (session) | Backend RAM — **lost on restart** |
| Operator UI overlay | Browser `localStorage` — survives refresh |
| Copilot RAG index | Backend RAM — rebuilt on startup + chat sync |
| `copilot_rag_fixture.json` | Disk cache for seed embeddings only |

Clear runtime overlay (browser console): `localStorage.removeItem('mbg.runtimeOverlay.v1')`

## Safety and Governance

AI output is **pre-verification**. Final decisions remain with authorized operators. Demo data is fictional. Copilot and scoring responses include governance notices.

## Known Limitations

- In-memory runtime; restart clears backend state (frontend overlay partially compensates)
- Copilot without API keys uses local embeddings + rules/keyword fallbacks
- Kimi Code keys may not work on all Moonshot embedding endpoints — use scoring/chat paths documented in `.env.example`
- PostgreSQL/Celery scaffolds exist but are not required for the demo path
- Ticket/case mutations in overlay are not a substitute for production persistence

## Next Development Phase

- Persist runtime cases/signals/tickets to PostgreSQL
- Authentication, RBAC, operator identity
- Production evidence storage and chain-of-custody
- Evaluated CV/OCR behind governed interfaces
- Satu Data–compatible integration contracts
- Expanded tests and CI/CD
