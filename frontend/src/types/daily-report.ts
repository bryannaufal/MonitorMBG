export interface PhotoVerification {
  photo_url: string;
  perceptual_hash?: string;
  is_duplicate: boolean;
  duplicate_of_report_id?: number;
  image_text_similarity?: number;
}

export interface DailyReport {
  id: number;
  title: string;
  description?: string;
  region: string;
  school_name?: string;
  menu_description?: string;
  portions_served?: number;
  cost_reported?: number;
  verification_status: "pending" | "verified" | "flagged" | "rejected";
  photo_urls: string[];
  photo_verifications: PhotoVerification[];
  created_at: string;
  updated_at?: string;
}

export interface DailyReportListResponse {
  items: DailyReport[];
  total: number;
  page: number;
  size: number;
}
