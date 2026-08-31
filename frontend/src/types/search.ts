export type SearchMode = "answered" | "related_docs";

export interface Citation {
  chunk_index: number;
  document_name: string;
  page_number: number | null;
  text: string;
  chroma_id: string;
}

export interface SearchRequest {
  query: string;
  top_k?: number;
}

export interface SearchResponse {
  search_id: string;
  query: string;
  answer: string;
  mode: SearchMode;
  citations: Citation[];
  latency_ms: number;
  token_count: number | null;
}

export interface SearchHistoryItem {
  id: string;
  query: string;
  answer: string | null;
  latency_ms: number | null;
  feedback: number | null;
  created_at: string;
}

export interface PaginatedSearchHistory {
  items: SearchHistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown> | null;
  };
}
