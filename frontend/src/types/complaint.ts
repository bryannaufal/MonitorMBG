export interface Complaint {
  id: number;
  text: string;
  source: "twitter" | "instagram" | "facebook" | "tiktok" | "news" | "other";
  source_url?: string;
  author?: string;
  region?: string;
  sentiment?: "positive" | "negative" | "neutral";
  sentiment_score?: number;
  topic_cluster?: string;
  status: "new" | "triaged" | "in_progress" | "resolved" | "dismissed";
  severity_score?: number;
  created_at: string;
  updated_at?: string;
}

export interface ComplaintListResponse {
  items: Complaint[];
  total: number;
  page: number;
  size: number;
}
