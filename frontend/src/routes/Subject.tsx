import { Link, useParams } from "react-router-dom";
import useSWR from "swr";
import { useState } from "react";
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
    <div className="max-w-6xl mx-auto px-4 py-10 grid grid-cols-1 md:grid-cols-[1fr_280px] gap-8">
      <div>
        <div className="flex items-start justify-between gap-3 mb-1">
          <h1 className="text-3xl font-semibold">{s.title}</h1>
          <div className="flex gap-2">
            {isAuthor && (
              <Link
                to={`/s/${s.slug}/edit`}
                className="text-sm bg-accent text-white px-3 py-1.5 rounded hover:bg-accent-ink"
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
                  className="border border-ink-300 rounded px-2 py-1 text-xs"
                  placeholder="new-slug"
                  value={forkSlug}
                  onChange={(e) => setForkSlug(e.target.value)}
                />
                <button className="text-sm border border-ink-300 px-3 py-1.5 rounded hover:bg-ink-100">
                  Fork
                </button>
              </form>
            )}
          </div>
        </div>
        <div className="text-sm text-ink-500 flex flex-wrap gap-3 mb-6">
          <span className="capitalize">{s.difficulty}</span>
          <span>{s.estimated_hours}h</span>
          <span>v{s.version}</span>
          <span className="capitalize">{s.status}</span>
          {s.forked_from && (
            <span>
              forked from{" "}
              <Link to={`/s/${s.forked_from.slug}`} className="text-accent hover:text-accent-ink">
                {s.forked_from.slug}
              </Link>{" "}
              @v{s.forked_from.version}
            </span>
          )}
        </div>

        <section className="prose-tight mb-8">
          <h2>Overview</h2>
          <LessonViewer markdown={s.overview} />
        </section>

        <section className="mb-8">
          <PrereqGraph nodes={prereqs.data?.nodes ?? []} />
        </section>

        <section>
          <h2 className="text-xs uppercase tracking-wider text-ink-500 mb-3">Lessons</h2>
          <ol className="space-y-2">
            {s.lessons.map((l) => (
              <li
                key={l.order}
                className="bg-white border border-ink-200 rounded-lg p-4"
              >
                <Link
                  to={`/s/${s.slug}/l/${l.order}`}
                  className="font-medium hover:text-accent"
                >
                  Lesson {l.order}: {l.title}
                </Link>
                <div className="text-xs text-ink-500 mt-1">
                  {l.estimated_minutes} minutes · {l.learning_objectives.length} learning objectives
                </div>
              </li>
            ))}
          </ol>
        </section>
      </div>

      <CoursePlayer slug={s.slug} lessons={lessonSummaries} />
    </div>
  );
}

function Loading() {
  return <div className="max-w-6xl mx-auto px-4 py-10 text-ink-400">Loading…</div>;
}
function NotFound() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-semibold mb-2">Subject not found</h1>
      <Link to="/" className="text-accent">Back to home</Link>
    </div>
  );
}
