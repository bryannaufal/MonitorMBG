# Phase 1.1 — Architecture Map: Report-to-Ticket Fusion Flow

Discovery only. Maps the existing implementation so the fusion workflow can be added safely.

## How the demo actually works
The frontend is fully self-sufficient on in-memory demo data. Every page calls
`getWithFallback(endpoint, fallback)` (`frontend/src/lib/api.ts`) — it tries
`http://localhost:8000`, and on any failure silently uses hardcoded fallback data.
The backend (`backend/app`, with Celery/alembic/vector-store scaffold) is **not needed
for the demo**. The single source of truth is `frontend/src/lib/demoFallback.ts` +
`frontend/src/types/monitoring.ts`.

Everything is **case-centric**: signals, reports, evidence, scores, tickets, and audit
events all carry a `case_id`, and `fallbackCases` assembles them into one `OversightCase`
per case. There is no standalone report or ticket detail page.

## Area → implementation → reuse point

| Area | Current implementation | Reuse for fusion flow |
|---|---|---|
| Report/complaint/daily list | All redirect to `/intake` ("Signal Inbox" table) | Entry point context |
| Report detail | None — reports are rows linking to `/cases/{caseId}` | Reuse case detail's SignalsTab |
| Evidence | `Evidence` type has `confidence_score`, `duplicate_score`, `image_text_match_score`; rendered in `cases/[id]` EvidenceTab | Card + score display = fusion-candidate row |
| Case ↔ signals/evidence | `fallbackCases` filters sub-entities by `case_id` | Join model to extend |
| Scoring / rationale | `ScoreResult.explanation` + `ScoreBar` component | Match-rationale + similarity already exist |
| Ticket list | `tickets/page.tsx` — cards, no create, no detail. `Ticket` has `linked_evidence_ids`, `audit_preview` | Enriched ticket target |
| Ticket status change | Optimistic setState → best-effort `api.patch` → revert on catch (`tickets` + `cases/[id]`) | Exact pattern to copy for confirm fusion |
| Audit trail | `AuditTrailEvent`; global page + per-case AuditTab | Prepend event on confirm |

## Current report-to-ticket flow
Does not exist interactively. Tickets are pre-generated in `fallbackTickets`. The intended
flow is only narrated statically in `simulation/page.tsx`. So the fusion flow is net-new.

## Recommended entry point for "Create ticket"
The case detail **TicketTab** empty state (`cases/[id]/page.tsx`) — it already renders a
`HelperPanel` when no ticket is linked. `updateTicketStatus` is the proven state pattern to
fork for confirm-fusion.

## Best UI primitive for the fusion-review screen
No modal/drawer/stepper/checkbox components exist in the repo. Use an inline tab/section with
reused evidence/signal cards + native `<input type="checkbox">`. Reusable primitives:
`PageHeader`, `HelperPanel`, `MetricTile`, `EntityChip`, `StatusBadge`, `GovernanceNote`,
`LoadingState`, `ScoreBar`.

## Audit event pattern
Follow `cases/[id]` `updateTicketStatus`: build an `AuditTrailEvent`, prepend to
`item.audit_events`; renders automatically in AuditTab and the global log.

## Questions / risks for Phase 1.2
1. "Similar reports" source — only one report per case in seed data; need same-vendor heuristic or extra seed rows.
2. `Report` has no evidence array and no match score — decide the similarity signal.
3. State is per-page `useState`, not shared — created ticket won't appear on `/tickets`. Acceptable for scripted demo.
4. Create-ticket needs a client-minted id.
5. Backend is optional — confirm frontend-only demo.
