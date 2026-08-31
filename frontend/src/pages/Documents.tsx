import { DocumentList } from "../components/documents/DocumentList";
import { FileUploader } from "../components/documents/FileUploader";
import { useDocuments } from "../hooks/useDocuments";

export function Documents() {
  const { documents, loading, error, upload, remove } = useDocuments();

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="text-xl font-semibold text-ink">Documents</h1>
      <p className="mt-1 text-sm text-stone-500">
        Upload is asynchronous — a document moves through pending → processing → ready.
      </p>

      <div className="mt-6">
        <FileUploader onUpload={upload} />
      </div>

      {error && <p className="mt-4 text-sm text-rose-600">{error}</p>}
      {loading ? (
        <p className="mt-6 text-sm text-stone-500">Loading…</p>
      ) : (
        <DocumentList documents={documents} onDelete={remove} />
      )}
    </div>
  );
}
