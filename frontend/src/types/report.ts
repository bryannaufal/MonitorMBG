export interface Report {
  id: number;
  title: string;
  description?: string;
  region: string;
  institution?: string;
  budget_reported?: number;
  portions_reported?: number;
  document_url?: string;
  ocr_extracted_text?: string;
  created_at: string;
  updated_at?: string;
}

export interface ReportListResponse {
  items: Report[];
  total: number;
  page: number;
  size: number;
}
