import { Link, Route, Routes } from "react-router-dom";
import useSWR from "swr";
import { Moon, Sun } from "lucide-react";
import Home from "./routes/Home";
import DomainView from "./routes/Domain";
import Subject from "./routes/Subject";
import LessonView from "./routes/Lesson";
import Edit from "./routes/Edit";
import { api, Me } from "./lib/api";
import LoginButton from "./components/LoginButton";
import { useDarkMode } from "./hooks/useDarkMode";

export default function App() {
  const me = useSWR<Me>("me", api.me, { shouldRetryOnError: false });
  const { isDark, toggle } = useDarkMode();

  return (
    <div className="min-h-screen flex flex-col dark:bg-ink-950">
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-ink-900/80 backdrop-blur-md border-b border-ink-200/50 dark:border-ink-800/50">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/" className="font-semibold tracking-tight text-lg dark:text-ink-50">
            <span className="text-accent dark:text-neon-violet">Human</span> Hivemind
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link
              to="/"
              className="text-ink-700 hover:text-ink-900 dark:text-ink-300 dark:hover:text-ink-50"
            >
              Browse
            </Link>
            <button
              type="button"
              onClick={toggle}
              aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
              className="inline-flex items-center justify-center w-8 h-8 rounded-md border border-ink-200 dark:border-ink-700 text-ink-700 dark:text-ink-200 hover:border-accent/50 dark:hover:border-neon-violet/50 hover:text-accent dark:hover:text-neon-violet transition-colors"
            >
              {isDark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
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
      <footer className="bg-white/60 dark:bg-ink-900/60 backdrop-blur-sm border-t border-ink-200 dark:border-ink-800 py-6 mt-12 text-center text-xs text-ink-500 dark:text-ink-400">
        Human Hivemind &middot; open-source courses for everything
      </footer>
    </div>
  );
}
