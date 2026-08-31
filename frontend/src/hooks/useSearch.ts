import { useCallback, useState } from "react";

import { extractErrorMessage } from "../services/api";
import { searchService } from "../services/searchService";
import type { SearchResponse } from "../types/search";

export function useSearch() {
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ask = useCallback(async (query: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await searchService.search({ query });
      setResult(response);
    } catch (err) {
      setError(extractErrorMessage(err));
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return { result, loading, error, ask };
}
