import { api } from "./api";
import type { PaginatedSearchHistory, SearchRequest, SearchResponse } from "../types/search";

export const searchService = {
  async search(request: SearchRequest): Promise<SearchResponse> {
    const { data } = await api.post<SearchResponse>("/search", request);
    return data;
  },

  async getHistory(limit = 20, offset = 0): Promise<PaginatedSearchHistory> {
    const { data } = await api.get<PaginatedSearchHistory>("/search/history", { params: { limit, offset } });
    return data;
  },
};
