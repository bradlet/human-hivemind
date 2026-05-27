import { Link, useParams } from "react-router-dom";
import useSWR from "swr";
import { useEffect, useState } from "react";
import { ChevronLeft } from "lucide-react";
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

  if (subject.isLoading)
    return (
      <div className="dark:bg-ink-950 min-h-screen">
        <div className="max-w-6xl mx-auto px-4 py-10 text-ink-400">Loading…</div>
      </div>
    );
  if (!subject.data)
    return (
      <div className="dark:bg-ink-950 min-h-screen">
        <div className="max-w-6xl mx-auto px-4 py-10 text-ink-900 dark:text-ink-100">
          Subject not found.
        </div>
      </div>
    );

  const s = subject.data;
  const lesson = s.lessons.find((l) => l.order === orderN);
  if (!lesson)
    return (
      <div className="dark:bg-ink-950 min-h-screen">
        <div className="max-w-6xl mx-auto px-4 py-10 text-ink-900 dark:text-ink-100">
          Lesson not found.
        </div>
      </div>
    );

  const idx = s.lessons.findIndex((l) => l.order === orderN);
  const prev = idx > 0 ? s.lessons[idx - 1] : null;
  const next = idx < s.lessons.length - 1 ? s.lessons[idx + 1] : null;
  const isAuthor = !!me.data && s.authors.some((a) => a.id === me.data!.id);

  return (
    <div className="dark:bg-ink-950 min-h-screen">
      <div className="max-w-6xl mx-auto px-4 py-10 grid grid-cols-1 md:grid-cols-[1fr_280px] gap-8">
        <div>
          <div className="text-sm mb-2">
            <Link
              to={`/s/${s.slug}`}
              className="inline-flex items-center gap-1 text-accent hover:text-violet-300 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              {s.title}
            </Link>
          </div>
          <h1 className="text-3xl font-semibold mb-1 text-ink-900 dark:text-ink-100">
            Lesson {lesson.order}: {lesson.title}
          </h1>
          <div className="text-xs text-ink-500 dark:text-ink-400 mb-6">
            {lesson.estimated_minutes} minutes
          </div>

          <section className="bg-accent-subtle dark:bg-accent/10 border border-accent/30 dark:border-accent/40 rounded-lg p-4 mb-8 dark:text-ink-200">
            <h3 className="text-xs uppercase tracking-wider text-accent-ink dark:text-accent mb-2">
              Learning objectives
            </h3>
            <ul className="list-disc pl-5 text-sm text-ink-800 dark:text-ink-200 space-y-1">
              {lesson.learning_objectives.map((o, i) => (
                <li key={i}>{o}</li>
              ))}
            </ul>
          </section>

          <LessonViewer markdown={lesson.body} />

          <div className="border-t border-ink-200 dark:border-ink-800 mt-10 pt-6 flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm text-ink-700 dark:text-ink-300 cursor-pointer">
              <input
                type="checkbox"
                className="accent-accent"
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
                  className="text-sm border border-ink-300 dark:border-ink-700 dark:text-ink-200 rounded px-3 py-1.5 hover:bg-ink-100 dark:hover:bg-ink-800"
                >
                  Edit this lesson
                </Link>
              )}
              {prev && (
                <Link
                  to={`/s/${s.slug}/l/${prev.order}`}
                  className="text-sm border border-ink-300 dark:border-ink-700 dark:text-ink-200 rounded px-3 py-1.5 hover:bg-ink-100 dark:hover:bg-ink-800"
                >
                  &larr; {prev.title}
                </Link>
              )}
              {next && (
                <Link
                  to={`/s/${s.slug}/l/${next.order}`}
                  className="text-sm bg-accent text-white rounded px-3 py-1.5 hover:bg-accent-ink glow-accent transition-shadow"
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
    </div>
  );
}
