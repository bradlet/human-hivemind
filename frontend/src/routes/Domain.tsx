import { Link, useParams } from "react-router-dom";
import useSWR from "swr";
import { useState } from "react";
import { ChevronLeft, BookOpen } from "lucide-react";
import { api } from "../lib/api";

const SORTS = [
  { value: "title", label: "Title" },
  { value: "updated_at", label: "Recently updated" },
  { value: "estimated_hours", label: "Estimated hours" },
  { value: "difficulty", label: "Difficulty" },
];

function capitalizeSlug(slug: string | undefined) {
  if (!slug) return "";
  return slug
    .split("-")
    .map((w) => (w.length > 0 ? w[0].toUpperCase() + w.slice(1) : w))
    .join(" ");
}

export default function DomainView() {
  const { slug } = useParams<{ slug: string }>();
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<string>("title");

  const subjects = useSWR(
    slug ? ["subjects", { domain: slug, search, sort }] : null,
    () => api.listSubjects({ domain: slug, search: search || undefined, sort }),
  );

  return (
    <div className="dark:bg-ink-950 min-h-screen">
      <div className="max-w-6xl mx-auto px-4 py-10">
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-sm text-accent hover:text-violet-300 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          All domains
        </Link>
        <h1 className="text-3xl font-semibold mt-2 mb-6 text-ink-900 dark:text-ink-100">
          {capitalizeSlug(slug)}
        </h1>

        <div className="flex flex-wrap items-center gap-3 mb-6">
          <input
            className="border border-ink-300 dark:border-ink-700 dark:bg-ink-800 dark:text-ink-100 dark:placeholder-ink-400 focus:ring-2 focus:ring-accent/40 focus:outline-none rounded px-3 py-2 text-sm flex-1 min-w-[200px]"
            placeholder="Filter by title…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select
            className="border border-ink-300 dark:border-ink-700 dark:bg-ink-800 dark:text-ink-100 focus:ring-2 focus:ring-accent/40 focus:outline-none rounded px-3 py-2 text-sm"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {subjects.isLoading && (
          <div className="text-ink-400 dark:text-ink-400">Loading…</div>
        )}
        {subjects.data && subjects.data.length === 0 && (
          <div className="text-ink-500 dark:text-ink-400">
            No subjects yet in this domain.
          </div>
        )}
        <ul className="grid gap-3 md:grid-cols-2">
          {subjects.data?.map((s) => (
            <li
              key={s.slug}
              className="bg-white dark:bg-ink-900 border border-ink-200 dark:border-ink-800 hover:border-accent/40 dark:hover:border-accent/60 transition-all hover:-translate-y-0.5 rounded-xl p-5"
            >
              <Link
                to={`/s/${s.slug}`}
                className="inline-flex items-center gap-2 font-medium text-ink-900 dark:text-ink-100 hover:text-accent dark:hover:text-accent"
              >
                <BookOpen className="w-4 h-4 text-accent" />
                {s.title}
              </Link>
              <div className="mt-3 flex flex-wrap gap-1.5">
                <span className="bg-ink-100 dark:bg-ink-800 text-ink-700 dark:text-ink-300 px-2 py-0.5 rounded-full text-xs">
                  {s.difficulty
                    ? s.difficulty[0].toUpperCase() + s.difficulty.slice(1)
                    : ""}
                </span>
                <span className="bg-ink-100 dark:bg-ink-800 text-ink-700 dark:text-ink-300 px-2 py-0.5 rounded-full text-xs">
                  {s.estimated_hours}h
                </span>
                <span className="bg-ink-100 dark:bg-ink-800 text-ink-700 dark:text-ink-300 px-2 py-0.5 rounded-full text-xs">
                  v{s.version}
                </span>
                <span className="bg-ink-100 dark:bg-ink-800 text-ink-700 dark:text-ink-300 px-2 py-0.5 rounded-full text-xs capitalize">
                  {s.status}
                </span>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
