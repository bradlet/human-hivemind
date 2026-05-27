import { Link, Route, Routes } from "react-router-dom";
import useSWR from "swr";
import Home from "./routes/Home";
import DomainView from "./routes/Domain";
import Subject from "./routes/Subject";
import LessonView from "./routes/Lesson";
import Edit from "./routes/Edit";
import { api, Me } from "./lib/api";
import LoginButton from "./components/LoginButton";

export default function App() {
  const me = useSWR<Me>("me", api.me, { shouldRetryOnError: false });

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-ink-200 bg-white">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/" className="font-semibold tracking-tight text-lg">
            <span className="text-accent">Human</span> Hivemind
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link to="/" className="text-ink-700 hover:text-ink-900">Browse</Link>
            <LoginButton me={me.data} loading={me.isLoading} />
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/d/:slug" element={<DomainView />} />
          <Route path="/s/:slug" element={<Subject />} />
          <Route path="/s/:slug/l/:order" element={<LessonView />} />
          <Route path="/s/:slug/edit" element={<Edit />} />
          <Route path="/s/:slug/l/:order/edit" element={<Edit />} />
        </Routes>
      </main>
      <footer className="border-t border-ink-200 bg-white py-6 mt-12 text-center text-xs text-ink-500">
        Human Hivemind &middot; open-source courses for everything
      </footer>
    </div>
  );
}
