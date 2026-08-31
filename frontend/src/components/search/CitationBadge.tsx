import { useState } from "react";

import type { Citation } from "../../types/search";

interface Props {
  citation: Citation;
}

/**
 * Renders one [N] marker. Clicking it reveals the exact source passage —
 * this is the frontend half of the citation mechanism documented in
 * system-design.md section 3: the backend maps [N] back to real chunk
 * metadata, and this component is where that metadata becomes visible
 * and verifiable to the user, not just trusted blindly.
 */
export function CitationBadge({ citation }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <span className="relative inline-block">
      <button
        onClick={() => setOpen((v) => !v)}
        className="mx-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-teal/10 px-1 text-xs font-semibold text-teal hover:bg-teal/20"
      >
        {citation.chunk_index}
      </button>
      {open && (
        <span className="absolute bottom-full left-1/2 z-10 mb-2 w-72 -translate-x-1/2 rounded-lg border border-stone-200 bg-white p-3 text-left text-xs shadow-lg">
          <span className="block font-medium text-ink">
            {citation.document_name}
            {citation.page_number != null && ` — Page ${citation.page_number}`}
          </span>
          <span className="mt-1 block text-stone-600">"{citation.text}"</span>
        </span>
      )}
    </span>
  );
}
