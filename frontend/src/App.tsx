import { Route, Routes } from "react-router-dom";

import { Header } from "./components/layout/Header";
import { Documents } from "./pages/Documents";
import { Search } from "./pages/Search";

export default function App() {
  return (
    <div className="min-h-screen">
      <Header />
      <Routes>
        <Route path="/" element={<Search />} />
        <Route path="/documents" element={<Documents />} />
      </Routes>
    </div>
  );
}
