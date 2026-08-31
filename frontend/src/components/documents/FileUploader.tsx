import { useCallback, useRef, useState } from "react";

const ALLOWED_EXTENSIONS = ["pdf", "docx", "txt", "md"];

interface Props {
  onUpload: (file: File) => Promise<unknown>;
}

export function FileUploader({ onUpload }: Props) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        setError(`Unsupported file type ".${ext}". Allowed: ${ALLOWED_EXTENSIONS.join(", ")}.`);
        return;
      }
      setError(null);
      setUploading(true);
      try {
        await onUpload(file);
      } finally {
        setUploading(false);
      }
    },
    [onUpload],
  );

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const file = e.dataTransfer.files[0];
          if (file) handleFile(file);
        }}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
          dragging ? "border-teal bg-teal/5" : "border-stone-300 hover:border-stone-400"
        }`}
      >
        <p className="text-sm font-medium text-ink">
          {uploading ? "Uploading…" : "Drop a document here, or click to browse"}
        </p>
        <p className="mt-1 text-xs text-stone-500">PDF, DOCX, TXT, or Markdown — up to 50MB</p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
            e.target.value = "";
          }}
        />
      </div>
      {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}
    </div>
  );
}
