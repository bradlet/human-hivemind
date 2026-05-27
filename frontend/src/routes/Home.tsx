import { Link } from "react-router-dom";
import useSWR from "swr";
import { api } from "../lib/api";
import DomainTree from "../components/DomainTree";

export default function Home() {
  const domains = useSWR("domains", api.domains);
  const featured = useSWR(["subjects", { sort: "updated_at" }], () =>
    api.listSubjects({ sort: "updated_at" }),
  );

  return (
    <div className="max-w-6xl mx-auto px-4 py-10 grid grid-cols-1 md:grid-cols-3 gap-10">
      <section className="md:col-span-1">
        <h2 className="text-xs uppercase tracking-wider text-ink-500 mb-3">Domains</h2>
        {domains.isLoading && <div className="text-ink-400">Loading…</div>}
        {domains.data && <DomainTree nodes={domains.data.domains} />}
      </section>

      <section className="md:col-span-2">
        <div className="mb-8">
          <h1 className="text-3xl font-semibold">Open-source courses for everything.</h1>
          <p className="text-ink-600 mt-2 max-w-prose">
            Every subject is a structured course: an overview, an ordered set of
            lessons with explicit learning objectives, and a graph of prerequisites.
            Pick a domain on the left, or jump into a recently updated subject below.
          </p>
        </div>
        <h2 className="text-xs uppercase tracking-wider text-ink-500 mb-3">
          Recently updated
        </h2>
        {featured.isLoading && <div className="text-ink-400">Loading…</div>}
        <ul className="space-y-2">
          {featured.data?.map((s) => (
            <li key={s.slug} className="bg-white rounded-lg border border-ink-200 p-4">
              <Link to={`/s/${s.slug}`} className="font-medium text-ink-900 hover:text-accent">
                {s.title}
              </Link>
              <div className="text-xs text-ink-500 mt-1 flex gap-3">
                <span>{s.difficulty}</span>
                <span>{s.estimated_hours}h</span>
                <span>v{s.version}</span>
                <span className="capitalize">{s.status}</span>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
