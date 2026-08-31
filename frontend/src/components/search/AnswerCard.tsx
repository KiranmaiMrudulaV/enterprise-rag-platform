import type { SearchResponse } from "../../types/search";
import { CitationBadge } from "./CitationBadge";

interface Props {
  result: SearchResponse;
}

const CITATION_PATTERN = /\[(\d+)\]/g;

/**
 * Splits the raw answer text on [N] markers and renders each marker as a
 * clickable CitationBadge, mirroring exactly how the backend's
 * AnswerParser (app/core/generation/answer_parser.py) identified them.
 */
function renderAnswerWithCitations(answer: string, citations: SearchResponse["citations"]) {
  const citationByIndex = new Map(citations.map((c) => [c.chunk_index, c]));
  const parts: (string | JSX.Element)[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = CITATION_PATTERN.exec(answer)) !== null) {
    const chunkIndex = Number(match[1]);
    const citation = citationByIndex.get(chunkIndex);

    parts.push(answer.slice(lastIndex, match.index));
    if (citation) {
      parts.push(<CitationBadge key={`${chunkIndex}-${match.index}`} citation={citation} />);
    } else {
      parts.push(match[0]); // unmapped marker — render as plain text rather than hiding it
    }
    lastIndex = match.index + match[0].length;
  }
  parts.push(answer.slice(lastIndex));

  return parts;
}

export function AnswerCard({ result }: Props) {
  const isRelatedDocs = result.mode === "related_docs";

  return (
    <div className="mt-6 rounded-lg border border-stone-200 bg-white p-5">
      {isRelatedDocs && (
        <p className="mb-3 rounded-md bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800">
          Low confidence — showing related passages instead of a direct answer.
        </p>
      )}
      <p className="text-sm leading-relaxed text-ink">{renderAnswerWithCitations(result.answer, result.citations)}</p>

      <div className="mt-4 flex items-center gap-4 border-t border-stone-100 pt-3 text-xs text-stone-400">
        <span>{result.latency_ms}ms</span>
        {result.token_count != null && <span>{result.token_count} tokens</span>}
        <span>{result.citations.length} source{result.citations.length === 1 ? "" : "s"}</span>
      </div>
    </div>
  );
}
