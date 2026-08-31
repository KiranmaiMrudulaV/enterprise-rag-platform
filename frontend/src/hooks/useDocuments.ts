import { useCallback, useEffect, useRef, useState } from "react";

import { documentService } from "../services/documentService";
import { extractErrorMessage } from "../services/api";
import type { DocumentResponse } from "../types/document";

const POLL_INTERVAL_MS = 2000;

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pollTimers = useRef<Record<string, ReturnType<typeof setInterval>>>({});

  const refresh = useCallback(async () => {
    try {
      const { items } = await documentService.list();
      setDocuments(items);
      setError(null);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timers = pollTimers.current;
    return () => {
      Object.values(timers).forEach(clearInterval);
    };
  }, [refresh]);

  /**
   * ADR-003: ingestion runs async. The frontend polls /status until the
   * document reaches a terminal state (ready|failed), then stops.
   */
  const pollUntilTerminal = useCallback(
    (documentId: string) => {
      if (pollTimers.current[documentId]) return;

      pollTimers.current[documentId] = setInterval(async () => {
        const result = await documentService.getStatus(documentId);
        setDocuments((prev) =>
          prev.map((doc) => (doc.id === documentId ? { ...doc, status: result.status, error_message: result.error_message } : doc)),
        );

        if (result.status === "ready" || result.status === "failed") {
          clearInterval(pollTimers.current[documentId]);
          delete pollTimers.current[documentId];
          refresh();
        }
      }, POLL_INTERVAL_MS);
    },
    [refresh],
  );

  const upload = useCallback(
    async (file: File) => {
      const doc = await documentService.upload(file);
      setDocuments((prev) => [doc, ...prev]);
      pollUntilTerminal(doc.id);
      return doc;
    },
    [pollUntilTerminal],
  );

  const remove = useCallback(async (id: string) => {
    await documentService.remove(id);
    setDocuments((prev) => prev.filter((doc) => doc.id !== id));
  }, []);

  return { documents, loading, error, upload, remove, refresh };
}
