export interface CostPlausibility {
  cost_per_portion?: number;
  standard_budget?: number;
  deviation_percent?: number;
  is_plausible?: boolean;
  notes?: string;
}

export interface ScoreResponse {
  report_id?: number;
  severity_score?: number;
  severity_level?: "low" | "medium" | "high" | "critical";
  confidence_score?: number;
  cost_plausibility?: CostPlausibility;
  contributing_factors: string[];
  computed_at?: string;
}

export interface ScoreListResponse {
  items: ScoreResponse[];
  total: number;
}
