export interface CopilotQuery {
  message: string;
  conversation_id?: string;
  context_filters?: Record<string, any>;
}

export interface SourceDocument {
  title: string;
  content_snippet: string;
  source_type: string;
  source_id: number;
  relevance_score: number;
}

export interface CopilotResponse {
  answer: string;
  sources: SourceDocument[];
  confidence: number;
  conversation_id?: string;
}
