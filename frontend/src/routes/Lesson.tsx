import { Link, useParams } from "react-router-dom";
import useSWR from "swr";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import CoursePlayer from "../components/CoursePlayer";
import LessonViewer from "../components/LessonViewer";
import { loadProgress, setLessonComplete } from "../lib/progress";

export default function LessonView() {
  const { slug, order } = useParams<{ slug: string; order: string }>();
  const orderN = Number(order);

  const subject = useSWR(slug ? ["subject", slug] : null, () => api.subject(slug!));
  const me = useSWR("me", api.me, { shouldRetryOnError: false });

  const [done, setDone] = useState(false);
  useEffect(() => {
    if (slug && Number.isFinite(orderN)) {
      setDone(loadProgress(slug).has(orderN));
    }
  }, [slug, orderN]);

  if (subject.isLoading) return <div className="max-w-6xl mx-auto px-4 py-10 text-ink-400">Loading…</div>;
  if (!subject.data) return <div className="max-w-6xl mx-auto px-4 py-10">Subject not found.</div>;

  const s = subject.data;
  const lesson = s.lessons.find((l) => l.order === orderN);
  if (!lesson) return <div className="max-w-6xl mx-auto px-4 py-10">Lesson not found.</div>;

  const idx = s.lessons.findIndex((l) => l.order === orderN);
  const prev = idx > 0 ? s.lessons[idx - 1] : null;
  const next = idx < s.lessons.length - 1 ? s.lessons[idx + 1] : null;
  const isAuthor = !!me.data && s.authors.some((a) => a.id === me.data!.id);

  return (
    <div className="max-w-6xl mx-auto px-4 py-10 grid grid-cols-1 md:grid-cols-[1fr_280px] gap-8">
      <div>
        <div className="text-sm mb-2">
          <Link to={`/s/${s.slug}`} className="text-accent hover:text-accent-ink">
            &larr; {s.title}
          </Link>
        </div>
        <h1 className="text-3xl font-semibold mb-1">
          Lesson {lesson.order}: {lesson.title}
        </h1>
        <div className="text-xs text-ink-500 mb-6">
          {lesson.estimated_minutes} minutes
        </div>

        <section className="bg-accent-subtle border border-accent/30 rounded-lg p-4 mb-8">
          <h3 className="text-xs uppercase tracking-wider text-accent-ink mb-2">
            Learning objectives
          </h3>
          <ul className="list-disc pl-5 text-sm text-ink-800 space-y-1">
            {lesson.learning_objectives.map((o, i) => (
              <li key={i}>{o}</li>
            ))}
          </ul>
        </section>

        <LessonViewer markdown={lesson.body} />

        <div className="border-t border-ink-200 mt-10 pt-6 flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-ink-700 cursor-pointer">
            <input
              type="checkbox"
              checked={done}
              onChange={(e) => {
                setDone(e.target.checked);
                setLessonComplete(s.slug, lesson.order, e.target.checked);
              }}
            />
            Mark as completed
          </label>
          <div className="flex gap-2">
            {isAuthor && (
              <Link
                to={`/s/${s.slug}/l/${lesson.order}/edit`}
                className="text-sm border border-ink-300 rounded px-3 py-1.5 hover:bg-ink-100"
              >
                Edit this lesson
              </Link>
            )}
            {prev && (
              <Link
                to={`/s/${s.slug}/l/${prev.order}`}
                className="text-sm border border-ink-300 rounded px-3 py-1.5 hover:bg-ink-100"
              >
                &larr; {prev.title}
              </Link>
            )}
            {next && (
              <Link
                to={`/s/${s.slug}/l/${next.order}`}
                className="text-sm bg-accent text-white rounded px-3 py-1.5 hover:bg-accent-ink"
              >
                {next.title} &rarr;
              </Link>
            )}
          </div>
        </div>
      </div>

      <CoursePlayer
        slug={s.slug}
        lessons={s.lessons.map((l) => ({
          order: l.order,
          title: l.title,
          estimated_minutes: l.estimated_minutes,
          learning_objectives: l.learning_objectives,
        }))}
        currentOrder={orderN}
      />
    </div>
  );
}
