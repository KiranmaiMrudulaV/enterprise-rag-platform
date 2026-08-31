import type { DocumentResponse } from "../../types/document";

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800",
  processing: "bg-blue-100 text-blue-800",
  ready: "bg-emerald-100 text-emerald-800",
  failed: "bg-rose-100 text-rose-800",
};

interface Props {
  document: DocumentResponse;
  onDelete: (id: string) => void;
}

export function DocumentCard({ document, onDelete }: Props) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-stone-200 bg-white p-4">
      <div>
        <p className="text-sm font-medium text-ink">{document.original_name}</p>
        <p className="mt-1 text-xs text-stone-500">
          {document.file_type.toUpperCase()} · {(document.file_size / 1024).toFixed(0)} KB ·{" "}
          {document.chunk_count} chunks
        </p>
        {document.status === "failed" && document.error_message && (
          <p className="mt-1 text-xs text-rose-600">{document.error_message}</p>
        )}
      </div>
      <div className="flex items-center gap-3">
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[document.status]}`}>
          {document.status}
        </span>
        <button
          onClick={() => onDelete(document.id)}
          className="text-xs text-stone-400 hover:text-rose-600"
          aria-label={`Delete ${document.original_name}`}
        >
          Delete
        </button>
      </div>
    </div>
  );
}
