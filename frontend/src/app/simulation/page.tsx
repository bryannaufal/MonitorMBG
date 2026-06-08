"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import {
  ArrowRight,
  Bot,
  CheckCircle2,
  ClipboardCheck,
  ClipboardList,
  FileSearch,
  GitBranch,
  History,
  LayoutDashboard,
  MessageSquareWarning,
  RadioTower,
  RotateCcw,
  Scale,
  ShieldAlert,
  UserCheck,
} from "lucide-react";

import GovernanceNote from "@/components/monitoring/GovernanceNote";
import { EntityChip, HelperPanel, MetricTile, PageHeader } from "@/components/monitoring/PageHeader";
import StatusBadge from "@/components/monitoring/StatusBadge";

type TimelineEvent = {
  id: string;
  step: number;
  timestamp: string;
  actor: string;
  role: string;
  action: string;
  badge: string;
};

const scenario = {
  id: "scenario-low-protein-late-delivery",
  title: "Low Protein Portion + Late Delivery Pattern",
  caseId: "case-001",
  ticketId: "tkt-001",
  vendorId: "vnd-001",
  vendorName: "SPPG Nusantara Sehat",
  school: "SDN Melati 03",
  region: "Jakarta Timur",
  reportId: "RPT-001",
  dailyReportId: "DR-001",
  scoreId: "SCR-001",
  complaintIds: ["COMP-001", "COMP-002"],
  evidenceIds: ["EVD-001", "EVD-002"],
  reporterType: "Parent",
  timestamp: "2026-06-04 10:15 WIB",
  description:
    "Menu hari ini hanya nasi, sayur sedikit, dan lauk telur sangat kecil. Makanan juga datang terlambat sekitar 45 menit.",
};

const steps = [
  { label: "Intake", icon: MessageSquareWarning },
  { label: "AI Analysis", icon: Bot },
  { label: "Fusion", icon: GitBranch },
  { label: "Scoring", icon: Scale },
  { label: "Case", icon: FileSearch },
  { label: "Ticket", icon: ClipboardList },
  { label: "Review", icon: UserCheck },
  { label: "Audit", icon: History },
  { label: "Update", icon: LayoutDashboard },
];

const baseEvents: TimelineEvent[] = [
  {
    id: "report-submitted",
    step: 1,
    timestamp: "2026-06-04 10:15 WIB",
    actor: "Parent Form",
    role: "Public channel",
    action: "Demo report submitted and linked to candidate vendor, school, and region.",
    badge: "Pre-verification signal",
  },
  {
    id: "ai-preverification",
    step: 2,
    timestamp: "2026-06-04 10:16 WIB",
    actor: "Demo AI Service",
    role: "AI Assistant",
    action: "AI-assisted classification, entity resolution, evidence checks, nutrition estimate, and cost plausibility generated.",
    badge: "AI-Assisted",
  },
  {
    id: "fusion-completed",
    step: 3,
    timestamp: "2026-06-04 10:17 WIB",
    actor: "Evidence Fusion Engine",
    role: "System",
    action: "Complaint, photo, official report, daily vendor report, and public complaint pattern fused into one case signal.",
    badge: "System Generated",
  },
  {
    id: "score-generated",
    step: 4,
    timestamp: "2026-06-04 10:18 WIB",
    actor: "Risk Scoring Service",
    role: "System",
    action: "Risk score generated with high priority recommendation; final decision remains human-led.",
    badge: "AI-Assisted",
  },
  {
    id: "case-created",
    step: 5,
    timestamp: "2026-06-04 10:19 WIB",
    actor: "Case Orchestration",
    role: "System",
    action: "case-001 selected as the oversight case connecting report, evidence, score, vendor, and ticket records.",
    badge: "System Generated",
  },
  {
    id: "ticket-created",
    step: 6,
    timestamp: "2026-06-04 10:20 WIB",
    actor: "Ticket Orchestration",
    role: "System",
    action: "tkt-001 created for Dinas Kesehatan Jakarta Timur with 24 hour SLA.",
    badge: "System Generated",
  },
  {
    id: "operator-reviewed",
    step: 7,
    timestamp: "2026-06-04 10:25 WIB",
    actor: "Demo Operator",
    role: "District Operator",
    action: "Operator reviewed the AI recommendation before any operational action was accepted.",
    badge: "Operator Reviewed",
  },
  {
    id: "audit-updated",
    step: 8,
    timestamp: "2026-06-04 10:26 WIB",
    actor: "Governance Logger",
    role: "System",
    action: "Governance log updated with report, AI, fusion, scoring, case, ticket, and operator actions.",
    badge: "Governance Log",
  },
  {
    id: "system-updated",
    step: 9,
    timestamp: "2026-06-04 10:27 WIB",
    actor: "Command Center Aggregator",
    role: "System",
    action: "Command Center metrics, ticket queue, vendor watchlist, and nutrition/cost anomaly counters updated.",
    badge: "System Generated",
  },
];

const pipeline = [
  {
    title: "NLP Classification",
    status: "AI-Assisted",
    rows: ["Detected issue: low protein portion, delivery delay", "Sentiment: negative", "Urgency: high"],
  },
  {
    title: "Entity Resolution",
    status: "Passed",
    rows: ["Vendor matched: SPPG Nusantara Sehat", "School matched: SDN Melati 03", "Region matched: Jakarta Timur"],
  },
  {
    title: "Evidence Check",
    status: "Needs Review",
    rows: ["Image-text match: partial match", "Duplicate photo risk: low", "Timestamp validity: valid", "OCR/document signal: menu text extracted / simulated"],
  },
  {
    title: "Nutrition Estimate",
    status: "Warning",
    rows: ["Protein estimate below expected range", "Calorie estimate borderline", "Portion adequacy: needs verification"],
  },
  {
    title: "Cost Plausibility",
    status: "Needs Review",
    rows: ["Cost per portion slightly above expected range", "Requires clarification"],
  },
];

const fusionRows = [
  ["Official report", "+20 confidence"],
  ["Photo evidence", "+15 confidence"],
  ["Daily vendor report mismatch", "+20 severity"],
  ["Repeated public complaints", "+20 severity"],
  ["Late delivery pattern", "+10 severity"],
  ["Low protein estimate", "+25 severity"],
  ["Incomplete clarification document", "-10 confidence"],
];

const scoreRows = [
  ["Severity Score", 86],
  ["Confidence Score", 78],
  ["Nutrition Concern Score", 82],
  ["Cost Anomaly Score", 64],
  ["Operational Risk Score", 73],
  ["Final Priority Score", 86],
];

const actionOptions = [
  "Schedule field verification",
  "Request vendor clarification first",
  "Escalate to regional supervisor",
];

export default function SimulationPage() {
  const [activeStep, setActiveStep] = useState(0);
  const [maxCompleted, setMaxCompleted] = useState(0);
  const [ticketStatus, setTicketStatus] = useState("New");
  const [operatorDecision, setOperatorDecision] = useState("Pending human review");
  const [modifiedAction, setModifiedAction] = useState(actionOptions[0]);
  const [extraEvents, setExtraEvents] = useState<TimelineEvent[]>([]);
  const [notice, setNotice] = useState("Demo scenario ready. Submit the report to begin the flow.");

  const visibleEvents = useMemo(() => {
    return [...baseEvents.filter((event) => event.step <= maxCompleted), ...extraEvents].sort(
      (a, b) => Date.parse(b.timestamp.replace(" WIB", "+07:00")) - Date.parse(a.timestamp.replace(" WIB", "+07:00")),
    );
  }, [extraEvents, maxCompleted]);

  function advance() {
    if (activeStep === steps.length - 1) {
      reset();
      return;
    }
    const nextCompleted = Math.max(maxCompleted, activeStep + 2);
    setMaxCompleted(nextCompleted);
    setActiveStep((current) => current + 1);
    setNotice(`${steps[activeStep].label} completed. ${steps[activeStep + 1].label} is ready for review.`);
  }

  function reset() {
    setActiveStep(0);
    setMaxCompleted(0);
    setTicketStatus("New");
    setOperatorDecision("Pending human review");
    setModifiedAction(actionOptions[0]);
    setExtraEvents([]);
    setNotice("Demo scenario reset. Submit the report to begin the flow.");
  }

  function addEvent(event: Omit<TimelineEvent, "id" | "timestamp">) {
    const timestamp = new Date().toLocaleString("sv-SE", { timeZone: "Asia/Jakarta" }).replace("T", " ");
    setExtraEvents((current) => [
      {
        ...event,
        id: `${event.action}-${Date.now()}`,
        timestamp: `${timestamp} WIB`,
      },
      ...current,
    ]);
  }

  function updateTicket(status: string) {
    setTicketStatus(status);
    setNotice(`Demo status updated: ${scenario.ticketId} moved to ${status}. Audit event generated.`);
    addEvent({
      step: 6,
      actor: "Demo Operator",
      role: "District Operator",
      action: `Ticket status updated to ${status}.`,
      badge: "Operator Reviewed",
    });
  }

  function decide(decision: "Accept" | "Reject") {
    const accepted = decision === "Accept";
    setOperatorDecision(accepted ? "Accepted recommendation: schedule field verification." : "Rejected recommendation; case remains under review.");
    setTicketStatus(accepted ? "Field Verification Scheduled" : "Under Review");
    setNotice(
      accepted
        ? "Human decision recorded. Field verification scheduled and governance event generated."
        : "Human decision recorded. Case remains under review and governance event generated.",
    );
    addEvent({
      step: 7,
      actor: "Demo Operator",
      role: "District Operator",
      action: accepted ? "Operator accepted AI recommendation and scheduled field verification." : "Operator rejected AI recommendation; case remains under review.",
      badge: "Operator Reviewed",
    });
    setMaxCompleted(Math.max(maxCompleted, 7));
  }

  function applyModifiedAction() {
    setOperatorDecision(`Modified recommendation: ${modifiedAction}.`);
    setTicketStatus(modifiedAction === "Schedule field verification" ? "Field Verification Scheduled" : "Waiting Vendor Clarification");
    setNotice("Operator modified the AI recommendation. Audit event generated.");
    addEvent({
      step: 7,
      actor: "Demo Operator",
      role: "District Operator",
      action: `Operator modified AI recommendation to: ${modifiedAction}.`,
      badge: "Operator Reviewed",
    });
    setMaxCompleted(Math.max(maxCompleted, 7));
  }

  const StepIcon = steps[activeStep].icon;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Oversight Flow Simulator"
        description="Simulate how MonitorMBG converts raw reports and evidence into prioritized, auditable oversight cases."
        breadcrumbs={[{ label: "Command Center", href: "/" }, { label: "Oversight Flow Simulator" }]}
        action={
          <div className="flex flex-wrap gap-2">
            <StatusBadge label="Demo scenario" />
            <StatusBadge label="AI-assisted simulation" />
          </div>
        }
      />
      <GovernanceNote compact />
      <HelperPanel>
        Human review required. This simulator uses deterministic demo intelligence for pre-verification, evidence fusion, scoring, and ticket action. It is not a final audit judgment and does not use real government data, real social scraping, OCR, CV inference, or production RAG.
      </HelperPanel>

      <section className="rounded-xl border border-border bg-surface-raised p-4">
        <div className="grid grid-cols-2 gap-2 md:grid-cols-9">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = activeStep === index;
            const isDone = maxCompleted >= index + 1;
            return (
              <button
                key={step.label}
                onClick={() => setActiveStep(index)}
                className={`flex min-h-[76px] flex-col items-start justify-between rounded-lg border p-3 text-left transition-colors ${
                  isActive
                    ? "border-brand-400 bg-brand-500/15 text-brand-100"
                    : isDone
                      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-100"
                      : "border-border bg-surface text-muted-foreground hover:border-brand-500/50"
                }`}
              >
                <span className="flex items-center gap-2 text-xs font-semibold uppercase">
                  <Icon className="h-4 w-4" />
                  {index + 1}
                </span>
                <span className="text-sm font-medium">{step.label}</span>
              </button>
            );
          })}
        </div>
      </section>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[320px_1fr_360px]">
        <aside className="space-y-4">
          <section className="rounded-xl border border-border bg-surface-raised p-5">
            <p className="text-xs uppercase text-muted-foreground">Primary scenario</p>
            <h2 className="mt-2 text-lg font-semibold">{scenario.title}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Fictional Indonesian MBG report linked to existing demo entities so generated outputs connect back to the app.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <EntityChip label={scenario.caseId} href={`/cases/${scenario.caseId}`} tone="case" />
              <EntityChip label={scenario.ticketId} tone="ticket" />
              <EntityChip label={scenario.vendorName} href={`/vendors/${scenario.vendorId}`} tone="vendor" />
            </div>
          </section>

          <section className="rounded-xl border border-border bg-surface-raised p-5">
            <h2 className="text-lg font-semibold">Simulation Progress</h2>
            <div className="mt-4 space-y-3">
              {steps.map((step, index) => (
                <button
                  key={step.label}
                  onClick={() => setActiveStep(index)}
                  className="flex w-full items-center justify-between gap-3 rounded-lg border border-border bg-surface p-3 text-left text-sm hover:border-brand-500/60"
                >
                  <span className="flex items-center gap-2">
                    {maxCompleted >= index + 1 ? <CheckCircle2 className="h-4 w-4 text-emerald-300" /> : <span className="h-4 w-4 rounded-full border border-border" />}
                    {step.label}
                  </span>
                  {activeStep === index ? <StatusBadge label="Current" /> : null}
                </button>
              ))}
            </div>
          </section>
        </aside>

        <main className="space-y-4">
          <section className="rounded-xl border border-border bg-surface-raised p-5">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <StepIcon className="h-5 w-5 text-brand-300" />
                  <StatusBadge label={`Step ${activeStep + 1}`} />
                  <StatusBadge label={steps[activeStep].label} />
                </div>
                <h2 className="mt-3 text-2xl font-semibold">{stepTitle(activeStep)}</h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{stepDescription(activeStep)}</p>
              </div>
              <button
                onClick={advance}
                className="inline-flex shrink-0 items-center gap-2 rounded-md bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-400"
              >
                {activeStep === 0 ? "Submit Demo Report" : activeStep === steps.length - 1 ? "Restart Scenario" : "Next Step"}
                {activeStep === steps.length - 1 ? <RotateCcw className="h-4 w-4" /> : <ArrowRight className="h-4 w-4" />}
              </button>
            </div>
          </section>

          {activeStep === 0 ? <IntakeStep /> : null}
          {activeStep === 1 ? <AiStep /> : null}
          {activeStep === 2 ? <FusionStep /> : null}
          {activeStep === 3 ? <ScoringStep /> : null}
          {activeStep === 4 ? <CaseStep /> : null}
          {activeStep === 5 ? <TicketStep ticketStatus={ticketStatus} onTicketAction={updateTicket} /> : null}
          {activeStep === 6 ? (
            <HumanReviewStep
              operatorDecision={operatorDecision}
              modifiedAction={modifiedAction}
              onModifiedAction={setModifiedAction}
              onAccept={() => decide("Accept")}
              onReject={() => decide("Reject")}
              onApplyModified={applyModifiedAction}
            />
          ) : null}
          {activeStep === 7 ? <AuditStep events={visibleEvents} /> : null}
          {activeStep === 8 ? <SystemUpdateStep ticketStatus={ticketStatus} operatorDecision={operatorDecision} /> : null}
        </main>

        <aside className="space-y-4">
          <section className="rounded-xl border border-border bg-surface-raised p-5">
            <div className="flex items-center gap-2">
              <RadioTower className="h-5 w-5 text-brand-300" />
              <h2 className="text-lg font-semibold">Generated Outputs</h2>
            </div>
            <p className="mt-3 rounded-lg border border-brand-500/25 bg-brand-500/10 p-3 text-sm text-brand-100">{notice}</p>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <MetricTile label="Confidence" value={maxCompleted >= 3 ? "78" : "--"} detail="Pre-verification" />
              <MetricTile label="Severity" value={maxCompleted >= 3 ? "86" : "--"} detail="Fusion result" />
              <MetricTile label="Priority" value={maxCompleted >= 4 ? "High" : "--"} detail="Human review required" />
              <MetricTile label="Ticket" value={ticketStatus} detail={scenario.ticketId} />
            </div>
          </section>

          <section className="rounded-xl border border-border bg-surface-raised p-5">
            <h2 className="text-lg font-semibold">Connected System Updates</h2>
            <div className="mt-4 space-y-2 text-sm">
              <SystemLink href="/" label="Command Center" detail="Active high-risk cases +1" done={maxCompleted >= 9} />
              <SystemLink href={`/cases/${scenario.caseId}`} label="Case Detail" detail={`${scenario.caseId} connected`} done={maxCompleted >= 5} />
              <SystemLink href="/tickets" label="Ticket Queue" detail={`${scenario.ticketId}: ${ticketStatus}`} done={maxCompleted >= 6} />
              <SystemLink href={`/vendors/${scenario.vendorId}`} label="Vendor Profile" detail="Watchlist learning updated" done={maxCompleted >= 9} />
              <SystemLink href="/audit-trail" label="Governance Log" detail={`${visibleEvents.length} visible events`} done={maxCompleted >= 8 || extraEvents.length > 0} />
            </div>
          </section>

          <section className="rounded-xl border border-border bg-surface-raised p-5">
            <h2 className="text-lg font-semibold">Latest Audit Events</h2>
            <div className="mt-4 space-y-3">
              {visibleEvents.slice(0, 5).length ? (
                visibleEvents.slice(0, 5).map((event) => (
                  <div key={event.id} className="rounded-lg border border-border bg-surface p-3">
                    <div className="flex flex-wrap gap-2">
                      <StatusBadge label={event.badge} />
                      <EntityChip label={scenario.caseId} tone="case" />
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">{event.action}</p>
                    <p className="mt-2 text-xs text-muted-foreground">{event.actor} - {event.timestamp}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">Audit events appear as the simulator runs.</p>
              )}
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

function stepTitle(index: number) {
  return [
    "Report Intake",
    "AI-Assisted Pre-Verification",
    "Evidence Fusion",
    "Risk Scoring",
    "Case Creation",
    "Ticket Orchestration",
    "Human-in-the-Loop Review",
    "Audit Trail Update",
    "Command Center Update",
  ][index];
}

function stepDescription(index: number) {
  return [
    "Reports can come from public complaints, official channels, school reports, or vendor daily evidence. MonitorMBG enriches and prioritizes their signals; it does not replace existing channels.",
    "The system simulates classification, entity matching, evidence checks, nutrition estimate, and cost plausibility as pre-verification signals.",
    "Independent sources are combined into one confidence and severity view so operators understand why a case is being prioritized.",
    "Scoring ranks the candidate case while preserving explanations, evidence concerns, and recommended next action.",
    "The candidate signal becomes a case-centered work item linked to existing evidence, ticketing, scoring, vendor, copilot, and audit views.",
    "Ticketing converts intelligence into accountable operational action with an assigned unit, SLA, and escalation path.",
    "AI recommends. A human operator accepts, modifies, or rejects the recommendation before operational action is treated as reviewed.",
    "The governance log records system-generated, AI-assisted, and operator-reviewed actions for traceability.",
    "The simulator closes the loop by showing how downstream dashboards, queues, vendor profiles, and anomaly counters are updated.",
  ][index];
}

function IntakeStep() {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <SectionCard title="Submitted Report">
        <Field label="Reporter Type" value={scenario.reporterType} />
        <Field label="School" value={scenario.school} />
        <Field label="Region" value={scenario.region} />
        <Field label="Vendor/SPPG" value={scenario.vendorName} />
        <Field label="Issue Category" value="Nutrition adequacy + Delivery delay" />
        <Field label="Evidence Attached" value="Meal photo, timestamp metadata, daily vendor report, repeated public complaints" />
        <Field label="Timestamp" value={scenario.timestamp} />
        <Field label="Source Confidence" value="Medium" />
      </SectionCard>
      <SectionCard title="Intake Output">
        <StatusLine label="Report received" status="Pre-verification signal" />
        <StatusLine label="Initial category: Nutrition adequacy + Delivery delay" status="Needs AI" />
        <StatusLine label="Linked candidate vendor: SPPG Nusantara Sehat" status="Passed" />
        <StatusLine label="Linked region: Jakarta Timur" status="Passed" />
        <StatusLine label="Status: Needs AI-assisted pre-verification" status="Human review required" />
        <p className="mt-4 rounded-lg border border-border bg-surface p-3 text-sm leading-6 text-muted-foreground">{scenario.description}</p>
      </SectionCard>
    </div>
  );
}

function AiStep() {
  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-100">
        AI-assisted pre-verification only. Final decision requires authorized operator review.
      </div>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {pipeline.map((item) => (
          <SectionCard key={item.title} title={item.title} badge={item.status}>
            <ul className="space-y-2 text-sm text-muted-foreground">
              {item.rows.map((row) => (
                <li key={row} className="rounded-lg bg-surface p-3">{row}</li>
              ))}
            </ul>
          </SectionCard>
        ))}
      </div>
    </div>
  );
}

function FusionStep() {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
      <SectionCard title="Evidence Fusion Inputs">
        <div className="space-y-2">
          {fusionRows.map(([label, impact]) => (
            <div key={label} className="flex items-center justify-between gap-3 rounded-lg bg-surface p-3 text-sm">
              <span className="text-muted-foreground">{label}</span>
              <span className={impact.startsWith("-") ? "font-semibold text-amber-200" : "font-semibold text-emerald-200"}>{impact}</span>
            </div>
          ))}
        </div>
      </SectionCard>
      <SectionCard title="Fusion Result">
        <ScoreBar label="Confidence Score" value={78} />
        <ScoreBar label="Severity Score" value={86} />
        <div className="mt-4 rounded-lg border border-red-500/25 bg-red-500/10 p-4">
          <StatusBadge label="High priority candidate case" />
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            Multiple independent signals raise confidence, while late delivery, low protein estimate, and daily report mismatch raise severity.
          </p>
        </div>
      </SectionCard>
      <SectionCard title="Relationship Map">
        <div className="space-y-2">
          {["Complaint", "Evidence", "Daily Report", "Vendor", "Case"].map((item, index) => (
            <div key={item} className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-full border border-brand-500/40 bg-brand-500/10 text-xs font-semibold text-brand-100">
                {index + 1}
              </span>
              <div className="flex-1 rounded-lg border border-border bg-surface p-3 text-sm">{item}</div>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}

function ScoringStep() {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
      <section className="rounded-xl border border-border bg-surface-raised p-5 xl:col-span-2">
        <h3 className="text-lg font-semibold">Scoring Breakdown</h3>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          {scoreRows.map(([label, value]) => (
            <ScoreBar key={label} label={String(label)} value={Number(value)} />
          ))}
        </div>
      </section>
      <SectionCard title="Recommended Action" badge="High">
        <p className="text-sm leading-6 text-muted-foreground">
          This case is ranked High because it combines repeated complaints, late delivery, low protein estimate, and daily report mismatch. Confidence is elevated by multiple independent signals, but operator review is required due to partial image-text match and incomplete vendor clarification.
        </p>
        <p className="mt-4 rounded-lg border border-brand-500/25 bg-brand-500/10 p-3 text-sm font-medium text-brand-100">
          Request vendor clarification and schedule field verification.
        </p>
      </SectionCard>
    </div>
  );
}

function CaseStep() {
  return (
    <SectionCard title="Created Case" badge="Human review required">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Field label="Case" value={scenario.caseId} />
        <Field label="Title" value={scenario.title} />
        <Field label="Vendor" value={scenario.vendorName} />
        <Field label="School" value={scenario.school} />
        <Field label="Region" value={scenario.region} />
        <Field label="Priority" value="High" />
        <Field label="Status" value="New / Under Review" />
        <Field label="Recommended Action" value="Request clarification and schedule field verification" />
      </div>
      <div className="mt-5 flex flex-wrap gap-2">
        <PrimaryLink href={`/cases/${scenario.caseId}`} label="Open Case Detail" />
        <SecondaryLink href={`/cases/${scenario.caseId}?tab=evidence`} label="View Evidence" />
        <SecondaryLink href="/scoring" label="Explain Score" />
        <SecondaryLink href="/copilot" label="Ask Copilot" />
        <SecondaryLink href={`/vendors/${scenario.vendorId}`} label="Open Vendor Profile" />
      </div>
    </SectionCard>
  );
}

function TicketStep({ ticketStatus, onTicketAction }: { ticketStatus: string; onTicketAction: (status: string) => void }) {
  const actions = ["Under Review", "Waiting Vendor Clarification", "Field Verification Scheduled", "Escalated"];
  return (
    <SectionCard title="Created Ticket" badge={ticketStatus}>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Field label="Ticket" value={scenario.ticketId} />
        <Field label="Linked Case" value={scenario.caseId} />
        <Field label="Assigned Unit" value="Dinas Kesehatan Jakarta Timur" />
        <Field label="SLA" value="24 hours" />
        <Field label="Escalation Level" value="Regional Supervisor" />
        <Field label="Recommended Action" value="Schedule field verification" />
      </div>
      <p className="mt-4 rounded-lg border border-border bg-surface p-3 text-sm text-muted-foreground">
        Ticketing converts intelligence into action while preserving evidence links, SLA, owner, and auditability.
      </p>
      <div className="mt-5 flex flex-wrap gap-2">
        {actions.map((action) => (
          <button
            key={action}
            onClick={() => onTicketAction(action)}
            className="rounded-md border border-border px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-surface hover:text-foreground"
          >
            {action}
          </button>
        ))}
        <PrimaryLink href="/tickets" label="Open Ticket Queue" />
      </div>
    </SectionCard>
  );
}

function HumanReviewStep({
  operatorDecision,
  modifiedAction,
  onModifiedAction,
  onAccept,
  onReject,
  onApplyModified,
}: {
  operatorDecision: string;
  modifiedAction: string;
  onModifiedAction: (value: string) => void;
  onAccept: () => void;
  onReject: () => void;
  onApplyModified: () => void;
}) {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <SectionCard title="AI Recommendation" badge="Not final audit judgment">
        <p className="text-sm leading-6 text-muted-foreground">
          Schedule field verification due to repeated nutrition complaints and late delivery pattern.
        </p>
        <div className="mt-4 rounded-lg border border-border bg-surface p-3 text-sm text-muted-foreground">
          Recommendation is a decision-support signal. Operator decision required.
        </div>
      </SectionCard>
      <SectionCard title="Operator Decision" badge="Human review required">
        <div className="flex flex-wrap gap-2">
          <button onClick={onAccept} className="rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">
            Accept Recommendation
          </button>
          <button onClick={onReject} className="rounded-md border border-border px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-surface">
            Reject Recommendation
          </button>
        </div>
        <div className="mt-4 flex flex-col gap-3 rounded-lg border border-border bg-surface p-3">
          <label className="text-sm font-medium">Modify Action</label>
          <select
            value={modifiedAction}
            onChange={(event) => onModifiedAction(event.target.value)}
            className="h-10 rounded-md border border-border bg-surface-raised px-3 text-sm outline-none focus:ring-1 focus:ring-brand-500"
          >
            {actionOptions.map((action) => (
              <option key={action} value={action}>{action}</option>
            ))}
          </select>
          <button onClick={onApplyModified} className="rounded-md border border-brand-500/40 px-3 py-2 text-sm font-medium text-brand-100 hover:bg-brand-500/10">
            Apply Modified Action
          </button>
        </div>
        <p className="mt-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-100">{operatorDecision}</p>
      </SectionCard>
    </div>
  );
}

function AuditStep({ events }: { events: TimelineEvent[] }) {
  return (
    <SectionCard title="Generated Audit Timeline" badge="Governance Log">
      <div className="space-y-3">
        {events.length ? (
          events.map((event) => (
            <div key={event.id} className="grid gap-3 rounded-lg border border-border bg-surface p-4 md:grid-cols-[170px_1fr_190px]">
              <div>
                <p className="text-xs text-muted-foreground">{event.timestamp}</p>
                <div className="mt-2"><StatusBadge label={event.badge} /></div>
              </div>
              <p className="text-sm leading-6 text-muted-foreground">{event.action}</p>
              <div className="text-sm">
                <p className="font-medium">{event.actor}</p>
                <p className="text-muted-foreground">{event.role}</p>
              </div>
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">Run the simulator steps to generate audit events.</p>
        )}
      </div>
      <div className="mt-5">
        <PrimaryLink href="/audit-trail" label="View Governance Log" />
      </div>
    </SectionCard>
  );
}

function SystemUpdateStep({ ticketStatus, operatorDecision }: { ticketStatus: string; operatorDecision: string }) {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <SectionCard title="Command Center Updated" badge="System Generated">
        <ul className="space-y-2 text-sm text-muted-foreground">
          {[
            "Active high-risk cases +1",
            "Jakarta Timur risk level increased",
            "SPPG Nusantara Sehat added to watchlist",
            "Ticket SLA started",
            "Audit trail updated",
            "Nutrition & Cost anomaly count updated",
          ].map((item) => (
            <li key={item} className="rounded-lg bg-surface p-3">{item}</li>
          ))}
        </ul>
      </SectionCard>
      <SectionCard title="Vendor Risk Learning" badge="Pre-verification signal">
        <p className="text-sm leading-6 text-muted-foreground">
          Vendor risk profile now reflects repeated issue categories, linked complaint IDs, daily report mismatch, ticket status, and operator decision.
        </p>
        <div className="mt-4 grid grid-cols-1 gap-3">
          <Field label="Ticket Status" value={ticketStatus} />
          <Field label="Operator Decision" value={operatorDecision} />
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          <PrimaryLink href="/" label="View Command Center" />
          <SecondaryLink href={`/cases/${scenario.caseId}`} label="Open Case Detail" />
          <SecondaryLink href={`/vendors/${scenario.vendorId}`} label="Open Vendor Profile" />
          <SecondaryLink href="/tickets" label="Open Ticket Queue" />
        </div>
      </SectionCard>
    </div>
  );
}

function SectionCard({ title, badge, children }: { title: string; badge?: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-border bg-surface-raised p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold">{title}</h3>
        {badge ? <StatusBadge label={badge} /> : null}
      </div>
      {children}
    </section>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-3">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium">{value}</p>
    </div>
  );
}

function StatusLine({ label, status }: { label: string; status: string }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-lg border border-border bg-surface p-3 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <StatusBadge label={status} />
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span className="font-semibold">{value}</span>
      </div>
      <div className="mt-3 h-2 rounded-full bg-surface-overlay">
        <div className="h-2 rounded-full bg-brand-500" style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
      </div>
    </div>
  );
}

function PrimaryLink({ href, label }: { href: string; label: string }) {
  return (
    <Link href={href} className="inline-flex items-center gap-2 rounded-md bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-400">
      {label}
      <ArrowRight className="h-4 w-4" />
    </Link>
  );
}

function SecondaryLink({ href, label }: { href: string; label: string }) {
  return (
    <Link href={href} className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-surface hover:text-foreground">
      {label}
      <ArrowRight className="h-4 w-4" />
    </Link>
  );
}

function SystemLink({ href, label, detail, done }: { href: string; label: string; detail: string; done: boolean }) {
  return (
    <Link href={href} className="flex items-start justify-between gap-3 rounded-lg border border-border bg-surface p-3 hover:border-brand-500/60">
      <span>
        <span className="block font-medium">{label}</span>
        <span className="mt-1 block text-xs text-muted-foreground">{detail}</span>
      </span>
      {done ? <ClipboardCheck className="h-4 w-4 text-emerald-300" /> : <ShieldAlert className="h-4 w-4 text-muted-foreground" />}
    </Link>
  );
}
