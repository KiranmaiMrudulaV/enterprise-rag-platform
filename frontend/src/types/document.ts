export type DocumentStatus = "pending" | "processing" | "ready" | "failed";

export interface DocumentResponse {
  id: string;
  original_name: string;
  file_type: string;
  file_size: number;
  status: DocumentStatus;
  chunk_count: number;
  error_message: string | null;
  created_at: string;
}

export interface PaginatedDocuments {
  items: DocumentResponse[];
  total: number;
  limit: number;
  offset: number;
}
