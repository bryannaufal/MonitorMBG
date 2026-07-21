# Phase 1.3 — Acceptance Criteria & Demo Scenarios

Implementation-readiness for the report-to-ticket fusion flow.

**Target case:** `case-001` / `vnd-001` (SPPG Nusantara Sehat)
**Editable files (Phase 2):** `frontend/src/app/cases/[id]/page.tsx`, `frontend/src/types/monitoring.ts`, `frontend/src/lib/demoFallback.ts` — nothing else.

## 1. Primary demo script — `case-001`

| # | Operator action | Expected result |
|---|---|---|
| 1 | Go to `/cases/case-001` | Case detail loads from fallback. |
| 2 | Click **Ticket** tab | Empty state, human-in-the-loop copy, "Create ticket" button (state = idle). |
| 3 | Click **Create ticket** | state = checking. "Checking related reports and evidence…" ~900ms, no network. |
| 4 | Wait | state = reviewing. "Suggested related items" (2 candidates) + evidence (≥2). Each: checkbox, match score, rationale. ≥1 report and ≥1 evidence pre-checked. |
| 5 | Review | Scores/rationales stable on re-render. |
| 6 | **Confirm fusion & create ticket** | state = created. Enriched ticket: TKT-001, status New, SLA, PIC, severity, linked report + evidence chips, fusion audit_preview. |
| 7 | Click a status button | Existing updateTicketStatus runs; status updates; status_changed audit event prepended. |
| 8 | Open **Audit trail** tab | fusion_approved event on top, actor "Demo Operator", role "District Operator", description names fused counts. |

## 2. Secondary scenarios
- **S1 Existing ticket** — seeded case (e.g. case-002) opens directly in created view; fusion skipped.
- **S2 No matches** — empty lists → standalone ticket copy; creation not blocked.
- **S3 Deselect** — unchecking a candidate reduces linked ids and audit counts accordingly.
- **S4 State locality** — created ticket lives only in case page state; not on `/tickets`. Accepted demo limitation.

## 3. Acceptance criteria (checklist)

**Governance / copy**
- [ ] idle empty state has human-in-the-loop framing.
- [ ] Candidate lists titled "Suggested related items".
- [ ] Confirm/created views state a pre-verification signal requiring human follow-up.
- [ ] No forbidden phrases (see §5).

**Behavior**
- [ ] Loading is visible and deterministic (fixed setTimeout, no Math.random, no fetch).
- [ ] Review lists candidates with native checkboxes; defaults pre-checked.
- [ ] Each candidate shows match score + ≥1 rationale; identical input → identical output.
- [ ] Enriched ticket has id TKT-001, case_id, status, sla, PIC, severity, linked report + evidence, fusion audit_preview.
- [ ] Confirm prepends one fusion_approved event with correct counts; visible in Audit tab.
- [ ] Existing status buttons still mutate the created ticket.
- [ ] Standalone path creates a ticket with empty linked arrays and counts of 0.

**Constraints**
- [ ] Zero network requests during the flow.
- [ ] No real AI/ML/NLP/OCR/embedding wording or logic.
- [ ] No new dependency, route, or store; changes in the 3 allowed files only.
- [ ] Ticket gains only optional linked_report_ids; seeded tickets unaffected.

## 4. Expected demo data — `case-001` (fictional, privacy-safe)

**2 related report/signal candidates for vnd-001** (distinct case_id from case-001):

| id | type | summary | vendor | location | date | fires | score | default |
|---|---|---|---|---|---|---|---|---|
| 4 | Public Complaint | "Porsi lauk kecil dan makanan datang terlambat di SDN Melati 03" | vnd-001 | SDN Melati 03, Jakarta Timur | 2026-06-03 (D-1) | vendor+category+location+date | ~95 | yes |
| 5 | Official Report | "Laporan pengawas: pengulangan porsi protein rendah pada SPPG Nusantara Sehat" | vnd-001 | Jakarta Timur | 2026-06-06 (D+2) | vendor+category+date | ~85 | yes |

**1 additional evidence candidate for case-001:**

| id | type | title | scores | fires | default |
|---|---|---|---|---|---|
| 3 | photo | "Foto porsi makan siang (indikasi duplikat)" | confidence 0.66, duplicate 0.78 | same case + high confidence + duplicate | yes (shows "possible duplicate — needs review") |

Guarantees ≥1 default-selected report and ≥1 default-selected evidence.

## 5. UX copy guardrails
**Must appear (conceptually):** "pre-verification", "operator reviewed"/"operator-approved",
"human follow-up required", "suggested related items".
**Must NOT appear:** "AI confirmed", "automatic violation", "fraud proven", "final decision",
or any wording implying the system replaces audits/inspections/government authority.
Reviewer: grep the diff for banned strings before merge.

## 6. Responsive QA matrix
Test all four TicketTab states at **320, 375, 768, 1024, 1440 px**, plus **125%** and **150%** zoom.
Confirm at each: no page-level horizontal scroll; checkboxes/buttons usable and unclipped;
ticket + candidate cards stack without overlap; long Indonesian copy wraps (`break-words`);
overflow confined to intended `overflow-x-auto` containers. Reuse existing responsive classes;
no fixed widths on new lists.

## 7. Phase 2 handoff
**Edit only:** `cases/[id]/page.tsx`, `types/monitoring.ts`, `demoFallback.ts`.
**Do NOT touch:** `lib/api.ts`, `getWithFallback`, global `/tickets` and `/audit-trail` pages,
`updateTicketStatus` (reuse, don't rewrite), layout/nav, backend.
**Order:** (1) seed data + optional Ticket field; (2) pure matching functions; (3) state machine
+ rendering with reused cards; (4) confirm → ticket + audit via setItem; (5) standalone path;
(6) copy + responsive pass.
**Manual QA routes:** `/cases/case-001` (primary + deselect), `/cases/case-002` (S1),
a no-match case (S2), `/tickets` (S4 — ticket absent, expected).
**Known risks / accepted limitations:** created ticket is page-local (S4) — do not build a store;
fixed 900ms loading is cosmetic, keep it; seed data keeps case-001 as the only rich happy path;
leave one deterministic-matching self-check behind (no framework).
