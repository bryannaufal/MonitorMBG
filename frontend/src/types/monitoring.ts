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

export interface Complaint {
  id: number;
  case_id: string;
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
  vendor_id: string;
  vendor_name: string;
  status: string;
  anomaly_tag?: string | null;
  created_at: string;
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
  report_id: number;
  type: string;
  title: string;
  linked_entity: string;
  ocr_result?: string | null;
  image_text_match_score?: number | null;
  duplicate_score?: number | null;
  confidence_score: number;
  ai_signal: string;
  reviewer_note: string;
  created_at: string;
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
  report_id: number;
  vendor_id: string;
  vendor_name: string;
  region: string;
  severity_score: number;
  confidence_score: number;
  nutrition_concern_score: number;
  cost_anomaly_score: number;
  anomaly_score: number;
  final_priority_score: number;
  priority_label: "Critical" | "High" | "Medium" | "Low" | string;
  explanation: string;
  recommended_action: string;
  computed_at: string;
  ai_notice: string;
}

export interface Ticket {
  id: string;
  case_id: string;
  title: string;
  status: string;
  sla: string;
  assigned_unit: string;
  escalation_level: string;
  linked_vendor_id: string;
  linked_vendor_name: string;
  linked_region: string;
  priority: number;
  recommended_action: string;
  linked_evidence_ids: number[];
  audit_preview: string;
  created_at: string;
  updated_at: string;
}

export interface AuditTrailEvent {
  id: number;
  case_id: string;
  ticket_id: string;
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
  title: string;
  priority_label: "Critical" | "High" | "Medium" | "Low" | string;
  status: string;
  vendor_id: string;
  vendor_name: string;
  region: string;
  district: string;
  school: string;
  issue_category: string;
  sla_status: string;
  assigned_unit: string;
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
  complaints: Complaint[];
  reports: Report[];
  daily_reports: DailyReport[];
  evidence: Evidence[];
  score: ScoreResult;
  ticket?: Ticket | null;
  copilot_sources: CaseSource[];
  audit_events: AuditTrailEvent[];
  ai_notice: string;
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
