import { Link, useParams } from "react-router-dom";
import useSWR from "swr";
import { useState } from "react";
import { Brain } from "lucide-react";
import { api } from "../lib/api";
import CoursePlayer from "../components/CoursePlayer";
import PrereqGraph from "../components/PrereqGraph";
import LessonViewer from "../components/LessonViewer";

export default function Subject() {
  const { slug } = useParams<{ slug: string }>();
  const subject = useSWR(slug ? ["subject", slug] : null, () => api.subject(slug!));
  const prereqs = useSWR(slug ? ["prereqs", slug] : null, () => api.prereqs(slug!));
  const me = useSWR("me", api.me, { shouldRetryOnError: false });

  const [forkSlug, setForkSlug] = useState("");

  if (subject.isLoading) return <Loading />;
  if (subject.error || !subject.data) return <NotFound />;
  const s = subject.data;
  const lessonSummaries = s.lessons.map((l) => ({
    order: l.order,
    title: l.title,
    estimated_minutes: l.estimated_minutes,
    learning_objectives: l.learning_objectives,
  }));
  const isAuthor =
    !!me.data && s.authors.some((a) => a.id === me.data!.id);

  return (
    <div className="dark:bg-ink-950 min-h-screen">
      <div className="max-w-6xl mx-auto px-4 py-10 grid grid-cols-1 md:grid-cols-[1fr_280px] gap-8">
        <div>
          <div className="flex items-start justify-between gap-3 mb-1">
            <h1 className="text-3xl font-semibold text-ink-900 dark:text-ink-100">
              {s.title}
            </h1>
            <div className="flex gap-2">
              {isAuthor && (
                <Link
                  to={`/s/${s.slug}/edit`}
                  className="text-sm bg-accent text-white px-3 py-1.5 rounded hover:bg-accent-ink glow-accent transition-shadow"
                >
                  Edit
                </Link>
              )}
              {!isAuthor && me.data && (
                <form
                  className="flex items-center gap-1"
                  onSubmit={async (e) => {
                    e.preventDefault();
                    const target = forkSlug || `${s.slug}-fork-${me.data!.id.slice(-4)}`;
                    const forked = await api.forkSubject(s.slug, target);
                    window.location.href = `/s/${forked.slug}`;
                  }}
                >
                  <input
                    className="border border-ink-300 dark:border-ink-700 dark:bg-ink-800 dark:text-ink-100 dark:placeholder-ink-400 focus:ring-2 focus:ring-accent/40 focus:outline-none rounded px-2 py-1 text-xs"
                    placeholder="new-slug"
                    value={forkSlug}
                    onChange={(e) => setForkSlug(e.target.value)}
                  />
                  <button className="text-sm border border-ink-300 dark:border-ink-700 dark:text-ink-200 px-3 py-1.5 rounded hover:bg-ink-100 dark:hover:bg-ink-800">
                    Fork
                  </button>
                </form>
              )}
            </div>
          </div>
          <div className="text-sm flex flex-wrap gap-1.5 mb-6 mt-3 items-center">
            <span className="bg-ink-100 dark:bg-ink-800 text-ink-700 dark:text-ink-300 px-2 py-0.5 rounded-full text-xs capitalize">
              {s.difficulty}
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
            {s.forked_from && (
              <span className="bg-accent/10 dark:bg-accent/20 text-accent dark:text-accent border border-accent/30 px-2 py-0.5 rounded-full text-xs">
                forked from{" "}
                <Link
                  to={`/s/${s.forked_from.slug}`}
                  className="hover:text-violet-300 underline underline-offset-2"
                >
                  {s.forked_from.slug}
                </Link>
                @v{s.forked_from.version}
              </span>
            )}
          </div>

          <section className="prose-tight mb-8">
            <h2 className="inline-flex items-center gap-2">
              <Brain className="w-5 h-5 text-accent" />
              Overview
            </h2>
            <LessonViewer markdown={s.overview} />
          </section>

          <section className="mb-8">
            <PrereqGraph nodes={prereqs.data?.nodes ?? []} />
          </section>

          <section>
            <h2 className="text-xs uppercase tracking-wider text-ink-500 dark:text-ink-400 mb-3">
              Lessons
            </h2>
            <ol className="space-y-2">
              {s.lessons.map((l) => (
                <li
                  key={l.order}
                  className="bg-white dark:bg-ink-900 border border-ink-200 dark:border-ink-800 border-l-2 hover:border-l-accent dark:hover:border-l-accent hover:border-accent/40 dark:hover:border-accent/60 transition-all rounded-lg p-4"
                >
                  <Link
                    to={`/s/${s.slug}/l/${l.order}`}
                    className="font-medium text-ink-900 dark:text-ink-100 hover:text-accent dark:hover:text-accent"
                  >
                    Lesson {l.order}: {l.title}
                  </Link>
                  <div className="text-xs text-ink-500 dark:text-ink-400 mt-1">
                    {l.estimated_minutes} minutes · {l.learning_objectives.length} learning objectives
                  </div>
                </li>
              ))}
            </ol>
          </section>
        </div>

        <CoursePlayer slug={s.slug} lessons={lessonSummaries} />
      </div>
    </div>
  );
}

function Loading() {
  return (
    <div className="dark:bg-ink-950 min-h-screen">
      <div className="max-w-6xl mx-auto px-4 py-10 text-ink-400">Loading…</div>
    </div>
  );
}
function NotFound() {
  return (
    <div className="dark:bg-ink-950 min-h-screen">
      <div className="max-w-6xl mx-auto px-4 py-10">
        <h1 className="text-2xl font-semibold mb-2 text-ink-900 dark:text-ink-100">
          Subject not found
        </h1>
        <Link to="/" className="text-accent hover:text-violet-300">
          Back to home
        </Link>
      </div>
    </div>
  );
}
