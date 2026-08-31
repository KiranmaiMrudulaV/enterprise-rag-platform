import { useState, type FormEvent } from "react";

interface Props {
  onSearch: (query: string) => void;
  loading: boolean;
}

export function SearchBar({ onSearch, loading }: Props) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim()) onSearch(query.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask a question about your company documents…"
        className="flex-1 rounded-lg border border-stone-300 px-4 py-3 text-sm focus:border-teal focus:outline-none focus:ring-1 focus:ring-teal"
      />
      <button
        type="submit"
        disabled={loading || !query.trim()}
        className="rounded-lg bg-teal px-5 py-3 text-sm font-medium text-white transition-opacity disabled:opacity-40"
      >
        {loading ? "Searching…" : "Ask"}
      </button>
    </form>
  );
}
