import type { DocumentResponse } from "../../types/document";
import { DocumentCard } from "./DocumentCard";

interface Props {
  documents: DocumentResponse[];
  onDelete: (id: string) => void;
}

export function DocumentList({ documents, onDelete }: Props) {
  if (documents.length === 0) {
    return <p className="mt-6 text-sm text-stone-500">No documents uploaded yet.</p>;
  }

  return (
    <div className="mt-6 flex flex-col gap-3">
      {documents.map((doc) => (
        <DocumentCard key={doc.id} document={doc} onDelete={onDelete} />
      ))}
    </div>
  );
}
