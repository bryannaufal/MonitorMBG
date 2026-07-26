export interface ListResponse<T> {
  items: T[];
  total: number;
  page?: number;
  size?: number;
}

export interface Vendor {
  id: string;
  name: string;
  region: string;
  district: string;
  assigned_schools: string[];
  daily_meal_volume: number;
  compliance_status: string;
  risk_score: number;
  risk_trend: number[];
  watchlist_status: "Critical" | "High" | "Medium" | "Low" | string;
  watchlist_reason: string;
  last_inspection_date: string;
  repeated_issue_categories: string[];
  coverage_notes: string;
  recommended_action: string;
  cases?: OversightCase[];
  linked_complaints?: Complaint[];
  linked_reports?: Report[];
  linked_daily_reports?: DailyReport[];
  ticket_history?: Ticket[];
  nutrition_cost_anomalies?: DailyReport[];
  audit_notes?: AuditTrailEvent[];
  ai_notice?: string;
}

export interface LocationDistrict {
  name: string;
  schools: string[];
  vendor_ids: string[];
}

export interface LocationRegistryEntry {
  province: string;
  districts: LocationDistrict[];
}

export interface AssignmentCandidate {
  id: string;
  name: string;
  role: string;
  provinces: string[];
  districts: string[];
  national: boolean;
}

export interface AssignmentOptions {
  locations: LocationRegistryEntry[];
  vendors: Vendor[];
  investigators: AssignmentCandidate[];
  units: AssignmentCandidate[];
  vendor_message?: string;
  manual_vendor: { id: string; label: string };
  governance_notice: string;
}

export interface Complaint {
  id: number;
  case_id: string | null;
  source: string;
  source_confidence: number;
  summary: string;
  text: string;
  issue_category: string;
  sentiment: string;
  severity_score: number;
  region: string;
  district: string;
  school: string;
  vendor_id: string | null;
  vendor_name: string;
  status: string;
  urgency?: string;
  anomaly_tag?: string | null;
  created_at: string;
}

/** Sinyal intake — sumber Kotak Masuk Sinyal. case_id null = belum dibentuk kasus. */
export interface Signal {
  id: number;
  case_id: string | null;
  source: string;
  source_confidence: number;
  urgency: string;
  status: string;
  summary: string;
  text: string;
  vendor_id: string | null;
  vendor_name: string;
  region: string;
  district: string;
  school: string;
  issue_category: string;
  created_at: string;
  // Lampiran foto opsional (mis. laporan resmi 4.jpg, unggahan media sosial 26.jpg).
  attachment_path?: string;
  attachment_title?: string;
  attachment_source?: string;
  attachment_note?: string;
  /** Runtime intake: public_form | scraper_fixture | scraper_live | scraper_twitter */
  intake_origin?: string;
}

export interface Report {
  id: number;
  case_id: string;
  report_code: string;
  reporter_type: string;
  school: string;
  region: string;
  district: string;
  vendor_id: string;
  vendor_name: string;
  submitted_at: string;
  summary: string;
  evidence_count: number;
  status: string;
  completeness_score: number;
  linked_ticket_id: string;
  linked_risk_score: number;
}

export interface DailyReport {
  id: number;
  case_id: string;
  vendor_id: string;
  vendor_name: string;
  school: string;
  region: string;
  planned_menu: string;
  actual_menu: string;
  delivery_timestamp: string;
  expected_timestamp: string;
  portion_count: number;
  photo_evidence_count: number;
  document_complete: boolean;
  photo_verification: string;
  verification_status: string;
  duplicate_indicator: boolean;
  mismatch_indicator: boolean;
  nutrition_estimate: NutritionEstimate;
  cost_estimate: {
    cost_per_portion: number;
    standard_budget: number;
    cost_anomaly_flag: boolean;
  };
  recommended_follow_up: string;
}

export interface Evidence {
  id: number;
  case_id: string;
  signal_id?: number | null;
  report_id?: number;
  type: string;
  title: string;
  file_path?: string;
  linked_entity: string;
  source?: string;
  ocr_result?: string | null;
  image_text_match_score?: number | null;
  duplicate_score?: number | null;
  confidence_score: number;
  review_status?: string;
  ai_signal?: string;
  reviewer_note: string;
  created_at: string;
  // Ditandai bila relasi bukti dilepas dari kasus (aset fisik tidak dihapus).
  unlinked_from_case?: boolean;
}

export interface NutritionEstimate {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface NutritionSummary {
  avg_calories: number;
  avg_protein_g: number;
  avg_carbs_g: number;
  avg_fat_g: number;
  total_reports_analyzed: number;
  flagged_reports: DailyReport[];
  ai_notice: string;
}

export interface NutritionResult {
  report_id: number;
  vendor_id: string;
  vendor_name: string;
  menu_estimate: string;
  planned_menu: string;
  nutrition_estimate: NutritionEstimate;
  portion_adequacy: string;
  nutrition_concern_score: number;
  cost_per_portion: number;
  cost_anomaly_flag: boolean;
  recommended_follow_up: string;
  ai_notice: string;
}

export interface ScoreResult {
  id: number;
  case_id: string;
  report_id?: number;
  vendor_id: string;
  vendor_name: string;
  region: string;
  severity_score: number;
  confidence_score: number;
  actionability_score: number;
  /** Estimasi kualitas gizi/porsi (0–100); null jika belum ada lampiran / penilaian vision. */
  nutrition_score?: number | null;
  final_priority_score: number;
  priority_label: "Critical" | "High" | "Medium" | "Low" | string;
  explanation: string;
  recommended_action: string;
  computed_at: string;
  ai_notice: string;
}

/** Live SLA indicator, derived on read by the backend ticketing engine. */
export type SlaState =
  | "on_track"
  | "at_risk"
  | "overdue"
  | "paused"
  | "met"
  | "breached"
  | "unknown";

export interface TicketNote {
  actor: string;
  note: string;
  at: string;
}

export interface Ticket {
  id: string;
  case_id: string;
  title: string;
  description?: string | null;
  status: string;
  /** Inherited from the parent case unless explicitly overridden. */
  severity?: string;
  impact?: string;
  urgency?: string;
  /** P1..P4; drives the SLA target and the due date. */
  sla_policy?: string;
  sla: string;
  assignee?: string | null;
  assignment_group?: string | null;
  assigned_unit: string;
  category?: string | null;
  labels?: string[];
  notes?: TicketNote[];
  escalation_level: string;
  linked_vendor_id: string;
  linked_vendor_name: string;
  linked_region: string;
  priority: number;
  priority_label?: string;
  priority_mode?: "suggested" | "manual" | "confirmed";
  origin?: "auto" | "manual";
  suggested_priority?: number;
  suggested_priority_label?: string;
  auto_ticket_reason?: string;
  recommended_action: string;
  linked_evidence_ids: number[];
  linked_report_ids?: number[];
  audit_preview: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
  /** Optional workstream label for a child ticket. */
  workstream?: string;
  due_at?: string | null;
  /** Derived fields from the SLA engine — present on API responses. */
  sla_state?: SlaState;
  hours_remaining?: number | null;
  overdue?: boolean;
  at_risk?: boolean;
  breached?: boolean;
}

export interface TicketSummary {
  total: number;
  open: number;
  in_progress: number;
  waiting: number;
  resolved: number;
  closed: number;
  completed: number;
  on_track: number;
  at_risk: number;
  overdue: number;
  paused: number;
  met_sla: number;
  breached_sla: number;
  unassigned: number;
}

export interface AuditTrailEvent {
  id: number;
  case_id: string | null;
  ticket_id: string | null;
  event_type: string;
  actor: string;
  role: string;
  description: string;
  timestamp: string;
}

export interface CaseSource {
  label: string;
  source_type: string;
  source_id: string | number;
  title: string;
}

export interface OversightCase {
  id: string;
  case_id: string;
  case_number: string;
  title: string;
  priority_label: "Critical" | "High" | "Medium" | "Low" | string;
  status: string;
  vendor_id: string;
  vendor_name: string;
  vendor_source_note?: string | null;
  region: string;
  district: string;
  school: string;
  issue_category: string;
  sla_status: string;
  assigned_unit: string;
  assigned_investigator?: string | null;
  recommended_action: string;
  summary: string;
  what_happened: string;
  why_it_matters: string;
  risk_explanation: string;
  signals_count: number;
  evidence_count: number;
  ticket_id?: string | null;
  created_at: string;
  updated_at: string;
  vendor: Vendor;
  signals: Signal[];
  complaints: Complaint[];
  reports: Report[];
  daily_reports: DailyReport[];
  evidence: Evidence[];
  score: ScoreResult;
  ticket?: Ticket | null;
  copilot_sources: CaseSource[];
  audit_events: AuditTrailEvent[];
  ai_notice: string;
  /** Case-centric fields. Optional so legacy demo snapshots remain readable. */
  case_type?: string;
  case_subtype?: string | null;
  impact_summary?: string;
  severity?: string;
  primary_owner?: string | null;
  handling_team?: string | null;
  secondary_owner?: string | null;
  watchers?: string[];
  due_at?: string | null;
  handling_strategy?: "direct" | "single_ticket" | "multi_ticket" | string;
  related_case_id?: string | null;
  case_relationship?: string | null;
  blockers?: string[];
  resolution_summary?: string | null;
  tickets?: Ticket[];
  ticket_summary?: TicketSummary;
}

export interface AnalyticsOverview {
  total_reports: number;
  public_signals: number;
  high_risk_cases: number;
  average_triage_time: string;
  ticket_response_rate: number;
  public_signal_spike: string;
  open_tickets: number;
  vendors_on_watchlist: number;
  ai_notice: string;
  top_region: string;
  /** Full ticket counters from the shared SLA engine. */
  ticket_summary?: TicketSummary;
}

export interface HeatmapRegion {
  region: string;
  district: string;
  risk_score: number;
  complaint_count: number;
  high_priority_cases: number;
  latitude: number;
  longitude: number;
}

export interface AnomalyHighlight {
  id: string;
  region: string;
  issue_category: string;
  description: string;
  severity: string;
  linked_vendor_id: string;
}

export interface TrendPoint {
  date: string;
  complaints: number;
  high_priority: number;
  avg_score: number;
}

export interface CopilotSource {
  title: string;
  content_snippet?: string;
  source_type: string;
  source_id: number | string;
  relevance_score: number;
}

export interface CopilotResponse {
  answer: string;
  sources: CopilotSource[];
  confidence: number;
  conversation_id?: string;
}
