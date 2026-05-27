import { Link, useParams } from "react-router-dom";
import useSWR from "swr";
import { useState } from "react";
import { api } from "../lib/api";

const SORTS = [
  { value: "title", label: "Title" },
  { value: "updated_at", label: "Recently updated" },
  { value: "estimated_hours", label: "Estimated hours" },
  { value: "difficulty", label: "Difficulty" },
];

export default function DomainView() {
  const { slug } = useParams<{ slug: string }>();
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<string>("title");

  const subjects = useSWR(
    slug ? ["subjects", { domain: slug, search, sort }] : null,
    () => api.listSubjects({ domain: slug, search: search || undefined, sort }),
  );

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      <Link to="/" className="text-sm text-accent hover:text-accent-ink">&larr; All domains</Link>
      <h1 className="text-3xl font-semibold mt-2 mb-6 capitalize">
        {slug?.replace(/-/g, " ")}
      </h1>

      <div className="flex flex-wrap items-center gap-3 mb-6">
        <input
          className="border border-ink-300 rounded px-3 py-2 text-sm flex-1 min-w-[200px]"
          placeholder="Filter by title…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="border border-ink-300 rounded px-3 py-2 text-sm"
          value={sort}
          onChange={(e) => setSort(e.target.value)}
        >
          {SORTS.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
      </div>

      {subjects.isLoading && <div className="text-ink-400">Loading…</div>}
      {subjects.data && subjects.data.length === 0 && (
        <div className="text-ink-500">No subjects yet in this domain.</div>
      )}
      <ul className="grid gap-3 md:grid-cols-2">
        {subjects.data?.map((s) => (
          <li key={s.slug} className="bg-white rounded-lg border border-ink-200 p-4">
            <Link to={`/s/${s.slug}`} className="font-medium hover:text-accent">
              {s.title}
            </Link>
            <div className="text-xs text-ink-500 mt-1 flex gap-3 capitalize">
              <span>{s.difficulty}</span>
              <span>{s.estimated_hours}h</span>
              <span>v{s.version}</span>
              <span>{s.status}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
