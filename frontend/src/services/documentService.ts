import { api } from "./api";
import type { DocumentResponse, DocumentStatus, PaginatedDocuments } from "../types/document";

export const documentService = {
  async upload(file: File): Promise<DocumentResponse> {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await api.post<DocumentResponse>("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  async list(limit = 20, offset = 0): Promise<PaginatedDocuments> {
    const { data } = await api.get<PaginatedDocuments>("/documents", { params: { limit, offset } });
    return data;
  },

  async getStatus(id: string): Promise<{ id: string; status: DocumentStatus; error_message: string | null }> {
    const { data } = await api.get(`/documents/${id}/status`);
    return data;
  },

  async remove(id: string): Promise<void> {
    await api.delete(`/documents/${id}`);
  },
};
