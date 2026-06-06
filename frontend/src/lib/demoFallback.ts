import type {
  AnalyticsOverview,
  AnomalyHighlight,
  AuditTrailEvent,
  Complaint,
  DailyReport,
  Evidence,
  HeatmapRegion,
  ListResponse,
  NutritionSummary,
  OversightCase,
  Report,
  ScoreResult,
  Ticket,
  TrendPoint,
  Vendor,
} from "@/types/monitoring";

export const demoNotice =
  "AI output is a pre-verification signal. Final decisions remain with authorized operators.";

export const fallbackOverview: AnalyticsOverview = {
  total_reports: 20,
  public_signals: 20,
  high_risk_cases: 7,
  average_triage_time: "18h",
  ticket_response_rate: 86,
  public_signal_spike: "+31%",
  open_tickets: 8,
  vendors_on_watchlist: 4,
  top_region: "DKI Jakarta",
  ai_notice: demoNotice,
};

export const fallbackVendors: Vendor[] = [
  {
    id: "vnd-001",
    name: "SPPG Gizi Nusantara Selatan",
    region: "DKI Jakarta",
    district: "Jakarta Selatan",
    assigned_schools: ["SDN Pejaten 03", "SMPN 182 Jakarta", "SDN Ragunan 07"],
    daily_meal_volume: 3280,
    compliance_status: "Under Review",
    risk_score: 88,
    risk_trend: [62, 68, 74, 81, 88],
    watchlist_status: "Critical",
    watchlist_reason: "Repeated low protein complaints, late delivery, and duplicate photo suspicion.",
    last_inspection_date: "2026-05-29",
    repeated_issue_categories: ["low protein portion", "delayed delivery", "duplicate photo"],
    coverage_notes: "High public-signal density in South Jakarta cluster.",
    recommended_action: "Escalate field verification within 24 hours and request replacement evidence.",
  },
  {
    id: "vnd-002",
    name: "Dapur Sehat Bandung Raya",
    region: "Jawa Barat",
    district: "Kota Bandung",
    assigned_schools: ["SDN Sukajadi 05", "SMPN 12 Bandung"],
    daily_meal_volume: 2410,
    compliance_status: "Needs Verification",
    risk_score: 79,
    risk_trend: [52, 56, 63, 72, 79],
    watchlist_status: "High",
    watchlist_reason: "Hygiene concern and suspected food poisoning signals from two channels.",
    last_inspection_date: "2026-05-25",
    repeated_issue_categories: ["hygiene concern", "suspected food poisoning", "cold food"],
    coverage_notes: "Two nearby schools reported similar symptoms within 48 hours.",
    recommended_action: "Coordinate health office inspection and temporarily increase sampling.",
  },
  {
    id: "vnd-004",
    name: "Dapur Mandiri Surabaya Timur",
    region: "Jawa Timur",
    district: "Surabaya",
    assigned_schools: ["SDN Rungkut Menanggal", "SMPN 35 Surabaya"],
    daily_meal_volume: 2875,
    compliance_status: "Escalated",
    risk_score: 83,
    risk_trend: [55, 61, 70, 77, 83],
    watchlist_status: "Critical",
    watchlist_reason: "Cost anomaly, missing fruit/milk, and repeated menu mismatch.",
    last_inspection_date: "2026-05-22",
    repeated_issue_categories: ["cost anomaly", "missing fruit/milk", "menu mismatch"],
    coverage_notes: "Reported cost above benchmark while menu completeness declined.",
    recommended_action: "Escalate to procurement review and conduct menu verification.",
  },
];

export const fallbackComplaints: Complaint[] = [
  {
    id: 1,
    case_id: "case-001",
    source: "School Hotline",
    source_confidence: 0.64,
    summary: "Low Protein Portion reported near SDN Pejaten 03",
    text: "Fictional demo signal: low protein portion pada distribusi MBG.",
    issue_category: "low protein portion",
    sentiment: "negative",
    severity_score: 82,
    region: "DKI Jakarta",
    district: "Jakarta Selatan",
    school: "SDN Pejaten 03",
    vendor_id: "vnd-001",
    vendor_name: "SPPG Gizi Nusantara Selatan",
    status: "Linked to Ticket",
    anomaly_tag: "Spike",
    created_at: "2026-06-02T08:15:00Z",
  },
  {
    id: 2,
    case_id: "case-002",
    source: "Parent Form",
    source_confidence: 0.72,
    summary: "Hygiene concern reported near SDN Sukajadi 05",
    text: "Fictional demo signal: hygiene concern and illness symptoms.",
    issue_category: "hygiene concern",
    sentiment: "negative",
    severity_score: 91,
    region: "Jawa Barat",
    district: "Kota Bandung",
    school: "SDN Sukajadi 05",
    vendor_id: "vnd-002",
    vendor_name: "Dapur Sehat Bandung Raya",
    status: "Under Review",
    anomaly_tag: "Spike",
    created_at: "2026-06-02T10:15:00Z",
  },
];

export const fallbackReports: Report[] = fallbackVendors.map((vendor, index) => ({
  id: index + 1,
  case_id: `case-00${index + 1}`,
  report_code: `RPT-MBG-2026-00${index + 1}`,
  reporter_type: index === 0 ? "School Operator" : "District Supervisor",
  school: vendor.assigned_schools[0],
  region: vendor.region,
  district: vendor.district,
  vendor_id: vendor.id,
  vendor_name: vendor.name,
  submitted_at: "2026-06-04T09:20:00Z",
  summary: `Official report package for ${vendor.name}.`,
  evidence_count: 4,
  status: vendor.compliance_status,
  completeness_score: 78 - index * 8,
  linked_ticket_id: `tkt-00${index + 1}`,
  linked_risk_score: vendor.risk_score,
}));

export const fallbackDailyReports: DailyReport[] = fallbackVendors.map((vendor, index) => ({
  id: index + 1,
  case_id: `case-00${index + 1}`,
  vendor_id: vendor.id,
  vendor_name: vendor.name,
  school: vendor.assigned_schools[0],
  region: vendor.region,
  planned_menu: "Nasi, ayam, sayur, buah, susu",
  actual_menu: index === 0 ? "Nasi, telur, sayur" : "Nasi, ayam, sayur, buah",
  delivery_timestamp: "2026-06-04T10:35:00Z",
  expected_timestamp: "2026-06-04T09:30:00Z",
  portion_count: Math.round(vendor.daily_meal_volume / vendor.assigned_schools.length),
  photo_evidence_count: 3,
  document_complete: index !== 1,
  photo_verification: index === 0 ? "Duplicate Suspected" : "Needs Verification",
  verification_status: index === 0 ? "Flagged" : "Under Review",
  duplicate_indicator: index === 0,
  mismatch_indicator: index !== 2,
  nutrition_estimate: { calories: 480 + index * 40, protein_g: 12 + index * 2, carbs_g: 60, fat_g: 12 },
  cost_estimate: { cost_per_portion: 16400 + index * 1300, standard_budget: 15000, cost_anomaly_flag: index === 2 },
  recommended_follow_up: vendor.recommended_action,
}));

export const fallbackEvidence: Evidence[] = [
  {
    id: 1,
    case_id: "case-001",
    report_id: 1,
    type: "photo",
    title: "Lunch plate photo evidence",
    linked_entity: "RPT-MBG-2026-001",
    image_text_match_score: 0.46,
    duplicate_score: 0.72,
    confidence_score: 0.62,
    ai_signal: "AI-assisted pre-verification",
    reviewer_note: "Menu text and image need human review.",
    created_at: "2026-06-04T08:05:00Z",
  },
  {
    id: 2,
    case_id: "case-001",
    report_id: 1,
    type: "document",
    title: "Invoice OCR simulation",
    linked_entity: "RPT-MBG-2026-001",
    ocr_result: "Simulated OCR: total and portion count extracted with medium confidence.",
    confidence_score: 0.7,
    ai_signal: "AI-assisted pre-verification",
    reviewer_note: "Invoice total needs operator confirmation.",
    created_at: "2026-06-04T08:25:00Z",
  },
];

export const fallbackScores: ScoreResult[] = fallbackVendors.map((vendor, index) => ({
  id: index + 1,
  case_id: `case-00${index + 1}`,
  report_id: index + 1,
  vendor_id: vendor.id,
  vendor_name: vendor.name,
  region: vendor.region,
  severity_score: vendor.risk_score,
  confidence_score: 72 - index * 4,
  nutrition_concern_score: 78 - index * 7,
  cost_anomaly_score: 65 + index * 6,
  anomaly_score: 82 - index * 5,
  final_priority_score: vendor.risk_score,
  priority_label: vendor.risk_score >= 80 ? "Critical" : "High",
  explanation: `${vendor.name} is prioritized because of ${vendor.watchlist_reason}`,
  recommended_action: vendor.recommended_action,
  computed_at: "2026-06-04T13:00:00Z",
  ai_notice: demoNotice,
}));

export const fallbackTickets: Ticket[] = fallbackScores.map((score, index) => ({
  id: `tkt-00${index + 1}`,
  case_id: score.case_id,
  title: `${score.priority_label} review: ${score.vendor_name}`,
  status: index === 0 ? "Escalated" : "Under Review",
  sla: "24h",
  assigned_unit: index === 2 ? "Procurement Review Desk" : "MBG Vendor Supervision Unit",
  escalation_level: score.priority_label,
  linked_vendor_id: score.vendor_id,
  linked_vendor_name: score.vendor_name,
  linked_region: score.region,
  priority: score.final_priority_score,
  recommended_action: score.recommended_action,
  linked_evidence_ids: [1, 2],
  audit_preview: "Ticket created from evidence fusion and queued for human review.",
  created_at: "2026-06-04T14:00:00Z",
  updated_at: "2026-06-04T15:00:00Z",
}));

export const fallbackAudit: AuditTrailEvent[] = fallbackTickets.map((ticket, index) => ({
  id: index + 1,
  case_id: ticket.case_id,
  ticket_id: ticket.id,
  event_type: index === 0 ? "escalation_triggered" : "ticket_created",
  actor: index === 0 ? "Supervisor Bima" : "Demo AI Service",
  role: index === 0 ? "Supervisor" : "AI Assistant",
  description: `${ticket.title} audit event. Human-in-the-loop review remains required.`,
  timestamp: ticket.updated_at,
}));

export const fallbackCases: OversightCase[] = fallbackScores.map((score, index) => {
  const vendor = fallbackVendors.find((item) => item.id === score.vendor_id) ?? fallbackVendors[0];
  const complaints = fallbackComplaints.filter((item) => item.case_id === score.case_id);
  const reports = fallbackReports.filter((item) => item.case_id === score.case_id);
  const daily_reports = fallbackDailyReports.filter((item) => item.case_id === score.case_id);
  const evidence = fallbackEvidence.filter((item) => item.case_id === score.case_id);
  const ticket = fallbackTickets.find((item) => item.case_id === score.case_id) ?? null;
  const audit_events = fallbackAudit.filter((item) => item.case_id === score.case_id);
  const issue = complaints[0]?.issue_category ?? vendor.repeated_issue_categories[0] ?? "routine monitoring";
  const school = reports[0]?.school ?? daily_reports[0]?.school ?? vendor.assigned_schools[0];
  return {
    id: score.case_id,
    case_id: score.case_id,
    title: `${issue.charAt(0).toUpperCase()}${issue.slice(1)} investigation at ${school}`,
    priority_label: score.priority_label,
    status: ticket?.status ?? vendor.compliance_status,
    vendor_id: vendor.id,
    vendor_name: vendor.name,
    region: vendor.region,
    district: vendor.district,
    school,
    issue_category: issue,
    sla_status: ticket ? `${ticket.sla} SLA` : "72h SLA",
    assigned_unit: ticket?.assigned_unit ?? "MBG Vendor Supervision Unit",
    recommended_action: score.recommended_action,
    summary: `MonitorMBG grouped public signals, official reports, daily vendor evidence, and scoring signals for ${vendor.name}.`,
    what_happened: `Signals for ${vendor.name} were grouped into ${score.case_id} after intake records showed ${issue}.`,
    why_it_matters: `The case affects ${school} in ${vendor.district}, ${vendor.region} and may indicate a recurring vendor risk pattern.`,
    risk_explanation: score.explanation,
    signals_count: complaints.length + reports.length + daily_reports.length,
    evidence_count: evidence.length,
    ticket_id: ticket?.id ?? null,
    created_at: reports[0]?.submitted_at ?? daily_reports[0]?.delivery_timestamp ?? score.computed_at,
    updated_at: ticket?.updated_at ?? score.computed_at,
    vendor,
    complaints,
    reports,
    daily_reports,
    evidence,
    score,
    ticket,
    copilot_sources: [
      { label: "Case", source_type: "case", source_id: score.case_id, title: score.case_id },
      { label: "Vendor", source_type: "vendor", source_id: vendor.id, title: vendor.name },
      { label: "Score", source_type: "score", source_id: score.id, title: `${score.case_id} score` },
    ],
    audit_events,
    ai_notice: demoNotice,
  };
}).sort((a, b) => b.score.final_priority_score - a.score.final_priority_score);

export const fallbackHeatmap: HeatmapRegion[] = fallbackVendors.map((vendor) => ({
  region: vendor.region,
  district: vendor.district,
  risk_score: vendor.risk_score,
  complaint_count: vendor.id === "vnd-001" ? 6 : 3,
  high_priority_cases: vendor.risk_score >= 75 ? 2 : 1,
  latitude: -6.2,
  longitude: 106.8,
}));

export const fallbackTrends: TrendPoint[] = [
  { date: "2026-05-30", complaints: 22, high_priority: 4, avg_score: 62 },
  { date: "2026-05-31", complaints: 28, high_priority: 5, avg_score: 67 },
  { date: "2026-06-01", complaints: 35, high_priority: 7, avg_score: 74 },
];

export const fallbackAnomalies: AnomalyHighlight[] = [
  {
    id: "ano-001",
    region: "DKI Jakarta",
    issue_category: "low protein portion",
    description: "Complaint volume rose above seven-day baseline.",
    severity: "High",
    linked_vendor_id: "vnd-001",
  },
];

export const fallbackNutritionSummary: NutritionSummary = {
  avg_calories: 512,
  avg_protein_g: 15.2,
  avg_carbs_g: 63,
  avg_fat_g: 12.4,
  total_reports_analyzed: fallbackDailyReports.length,
  flagged_reports: fallbackDailyReports,
  ai_notice: demoNotice,
};

export const asList = <T>(items: T[]): ListResponse<T> => ({
  items,
  total: items.length,
  page: 1,
  size: items.length,
});
