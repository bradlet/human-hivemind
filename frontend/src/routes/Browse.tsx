import { Link } from "react-router-dom";
import useSWR from "swr";
import { Clock } from "lucide-react";
import { api } from "../lib/api";
import DomainCardBrowser from "../components/DomainCardBrowser";

export default function Browse() {
  const domains = useSWR("domains", api.domains);
  const featured = useSWR(["subjects", { sort: "updated_at" as const }], () =>
    api.listSubjects({ sort: "updated_at" }),
  );

  return (
    <div className="dark:bg-ink-950 min-h-screen">
      <div className="max-w-6xl mx-auto px-4 py-12">
        <header className="mb-10">
          <div className="text-[10px] uppercase tracking-[0.4em] text-accent dark:text-neon-violet mb-3">
            Browse
          </div>
          <h1 className="text-4xl md:text-5xl font-light tracking-tight text-ink-900 dark:text-ink-50">
            Explore the knowledge graph.
          </h1>
          <p className="mt-3 text-ink-600 dark:text-ink-400 max-w-2xl">
            Pick a domain to expand its children. Use "View list" on any card
            for the traditional list view of subjects in that domain.
          </p>
        </header>

        <section className="py-4">
          {domains.data && <DomainCardBrowser nodes={domains.data.domains} />}
        </section>

        <section className="mt-20">
          <div className="flex items-center gap-2 mb-6">
            <Clock size={16} className="text-accent dark:text-neon-violet" />
            <h2 className="text-2xl font-semibold tracking-tight text-ink-900 dark:text-ink-50">
              Recently updated
            </h2>
          </div>

          {featured.isLoading && (
            <div className="text-ink-400 dark:text-ink-500">Loading…</div>
          )}

          <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {featured.data?.map((s) => (
              <li key={s.slug}>
                <Link
                  to={`/s/${s.slug}`}
                  className="block bg-white dark:bg-ink-900 border border-ink-200 dark:border-ink-800 hover:border-accent/40 dark:hover:border-accent/60 rounded-xl p-5 transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-accent/5"
                >
                  <div className="font-medium text-lg text-ink-900 dark:text-ink-50 leading-snug">
                    {s.title}
                  </div>
                  <div className="mt-4 flex flex-wrap gap-1.5">
                    <Pill>{s.difficulty}</Pill>
                    <Pill>{s.estimated_hours}h</Pill>
                    <Pill>v{s.version}</Pill>
                    <Pill className="capitalize">{s.status}</Pill>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}

function Pill({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={
        "inline-flex items-center text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full border border-ink-200 dark:border-ink-700 text-ink-600 dark:text-ink-300 bg-ink-50 dark:bg-ink-800/60 " +
        (className ?? "")
      }
    >
      {children}
    </span>
  );
}
