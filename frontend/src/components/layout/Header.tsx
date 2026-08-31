import { NavLink } from "react-router-dom";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-2 text-sm font-medium rounded-md transition-colors ${
    isActive ? "bg-teal text-white" : "text-stone-600 hover:bg-stone-100"
  }`;

export function Header() {
  return (
    <header className="border-b border-stone-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <div>
          <p className="text-lg font-semibold text-ink">Enterprise RAG Platform</p>
          <p className="text-xs text-stone-500">Ask questions, get cited answers.</p>
        </div>
        <nav className="flex gap-2">
          <NavLink to="/" end className={linkClass}>
            Search
          </NavLink>
          <NavLink to="/documents" className={linkClass}>
            Documents
          </NavLink>
        </nav>
      </div>
    </header>
  );
}
