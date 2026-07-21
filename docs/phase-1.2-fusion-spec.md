# Phase 1.2 — Deterministic Report-to-Ticket Fusion Spec

Implementation-ready design for the create-ticket fusion flow.

## Scope
All work in one file: `frontend/src/app/cases/[id]/page.tsx`. No new routes, backend, or deps.
Matching reads existing exports from `demoFallback.ts`. All state is client-side on the case
page, following the existing `updateTicketStatus` optimistic pattern.

## UX flow (inline in TicketTab, no modal)
1. **idle** — empty state + "Create ticket" button, human-in-the-loop copy.
2. **checking** — ~900ms `setTimeout` loading: "Checking related reports and evidence…". No real async.
3. **reviewing** — two lists (related reports/signals, evidence) as reused cards with native checkboxes, a match-rationale line, and a match-score `EntityChip`. Default-selected candidates pre-checked. Buttons: "Confirm fusion & create ticket" and "Create standalone ticket".
4. **created** — normal ticket view + "Fused from N reports · M evidence" summary + appended audit note. Existing status buttons work unchanged.

## State machine (local to case page)
```ts
type FusionState = "idle" | "checking" | "reviewing" | "created";
const [fusionState, setFusionState] = useState<FusionState>(item.ticket ? "created" : "idle");
```
- idle → checking: click. setTimeout(900) → compute candidates → reviewing.
- reviewing → created: confirm/standalone → build ticket + audit event → setItem → created.
- item.ticket already present on load → start in created.

## Candidate matching rules (deterministic, pure functions)

**Related reports/signals** — scan reports + complaints + daily reports, exclude items already
in the case. Score = sum of weights, capped 95. Default-selected if score ≥ 70.

| Rule | Condition | Weight | Rationale |
|---|---|---|---|
| Same vendor (SPPG) | `vendor_id === case.vendor_id` | 45 | "Same SPPG vendor as this case" |
| Same category | `issue_category === case.issue_category` | 25 | "Matches issue category: {cat}" |
| Same location | `district === case.district` | 15 | "Same regency: {district}" |
| Nearby date | `abs(days) ≤ 3` | 15 | "Reported within 3 days of this case" |

**Evidence** — scan evidence, exclude items already linked. Default-selected if
`confidence_score ≥ 0.6`.

| Rule | Condition | Weight | Rationale |
|---|---|---|---|
| Same case | `case_id === case.case_id` | 40 | "Already attached to this case" |
| Linked report | `report_id ∈ candidate report ids` | 30 | "Belongs to a related report" |
| High confidence | `confidence_score ≥ 0.6` | 20 | "Confidence {n}% (pre-verification)" |
| Duplicate flag | `duplicate_score ≥ 0.7` | 10 | "Possible duplicate — needs review" |

`vendor_id` is the SPPG proxy (no `sppg_id` field exists). No AI/NLP/OCR/embeddings.

## Candidate display model (UI-only types)
```ts
interface FusionReportCandidate {
  id: number; sourceType: string; summary: string; vendorName: string;
  location: string; date: string; matchScore: number; rationale: string[]; defaultSelected: boolean;
}
interface FusionEvidenceCandidate {
  id: number; type: string; title: string; score: number;
  linkedTo: string; rationale: string[]; defaultSelected: boolean;
}
```

## Ticket created on confirm (deterministic id)
```ts
const ticket: Ticket = {
  id: `TKT-${item.case_id.replace("case-", "")}`,       // "TKT-001"
  case_id: item.case_id,
  title: `${item.priority_label} review: ${item.vendor_name}`,
  status: "New",
  sla: item.priority_label === "Critical" ? "24h" : "48h",
  assigned_unit: item.assigned_unit,                     // PIC
  escalation_level: item.priority_label,
  linked_vendor_id: item.vendor_id,
  linked_vendor_name: item.vendor_name,
  linked_region: item.region,
  priority: item.score.final_priority_score,
  recommended_action: item.score.recommended_action,
  linked_evidence_ids: selected.evidence,
  audit_preview: `Created after operator-approved fusion of ${nReports} report(s) and ${nEvidence} evidence item(s). Pre-verification signal — human follow-up required.`,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};
```
**One small type change:** add optional `linked_report_ids?: number[]` to the `Ticket`
interface in `types/monitoring.ts` (optional → no impact on seeded tickets).

## Audit event on confirm
```ts
{ id: Date.now(), case_id: item.case_id, ticket_id: ticket.id,
  event_type: "fusion_approved", actor: "Demo Operator", role: "District Operator",
  description: `Operator approved fusion of ${nReports} related report(s) and ${nEvidence} evidence item(s) while creating ticket ${ticket.id}. Pre-verification result — final decision requires authorized human review.`,
  timestamp: new Date().toISOString() }
```
`classifyEvent` already tags Operator roles as "Operator Reviewed" — no change needed.

## Empty / no-match behavior
- Both lists empty → "No related reports or evidence were found automatically. You can still create a standalone ticket for human follow-up." + "Create standalone ticket".
- Standalone ticket = same object with empty linked arrays, counts of 0.
- Never block creation on zero matches.

## Happy-path demo target
`case-001` / `vnd-001`. Phase 2 adds 2 fictional same-vendor reports + 1 evidence row to
`demoFallback.ts` so this case shows a rich candidate list.

## Code paths Phase 2 edits
- `frontend/src/app/cases/[id]/page.tsx` — TicketTab state machine, candidate compute, confirm handler.
- `frontend/src/types/monitoring.ts` — add optional `linked_report_ids?: number[]`.
- `frontend/src/lib/demoFallback.ts` — add fictional same-vendor rows for `case-001`.
