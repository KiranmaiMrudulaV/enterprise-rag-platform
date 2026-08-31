import { AnswerCard } from "../components/search/AnswerCard";
import { SearchBar } from "../components/search/SearchBar";
import { useSearch } from "../hooks/useSearch";

export function Search() {
  const { result, loading, error, ask } = useSearch();

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="text-xl font-semibold text-ink">Ask a question</h1>
      <p className="mt-1 text-sm text-stone-500">
        Answers are grounded in your uploaded documents, with clickable citations to the exact source.
      </p>

      <div className="mt-6">
        <SearchBar onSearch={ask} loading={loading} />
      </div>

      {error && <p className="mt-4 text-sm text-rose-600">{error}</p>}
      {result && <AnswerCard result={result} />}
    </div>
  );
}
