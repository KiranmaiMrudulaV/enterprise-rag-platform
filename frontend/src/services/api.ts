import axios, { AxiosError } from "axios";

import type { ApiErrorResponse } from "../types/search";

export const api = axios.create({
  baseURL: "/api/v1",
  timeout: 30_000,
});

/**
 * Every backend error follows the structured envelope from RFC-001:
 * { error: { code, message, details } }. This normalizes any thrown
 * error into a plain message string components can render directly,
 * without each call site needing to know the envelope shape.
 */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorResponse>;
    const envelope = axiosError.response?.data?.error;
    if (envelope?.message) return envelope.message;
  }
  return "Something went wrong. Please try again.";
}
