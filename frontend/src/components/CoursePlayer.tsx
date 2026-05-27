import { Link, useParams } from "react-router-dom";
import type { LessonSummary } from "../lib/api";
import { loadProgress } from "../lib/progress";

export default function CoursePlayer({
  slug,
  lessons,
  currentOrder,
}: {
  slug: string;
  lessons: LessonSummary[];
  currentOrder?: number;
}) {
  const completed = loadProgress(slug);
  const total = lessons.length;
  const done = lessons.filter((l) => completed.has(l.order)).length;
  return (
    <aside className="bg-white border border-ink-200 rounded-lg p-4 sticky top-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs uppercase tracking-wider text-ink-500">Lessons</h3>
        <span className="text-xs text-ink-500">{done}/{total}</span>
      </div>
      <div className="h-1 w-full bg-ink-200 rounded mb-3 overflow-hidden">
        <div
          className="h-full bg-accent transition-all"
          style={{ width: `${total ? (done / total) * 100 : 0}%` }}
        />
      </div>
      <ol className="space-y-1 text-sm">
        {lessons.map((l) => {
          const isCurrent = l.order === currentOrder;
          const isDone = completed.has(l.order);
          return (
            <li key={l.order}>
              <Link
                to={`/s/${slug}/l/${l.order}`}
                className={
                  "flex items-center gap-2 px-2 py-1.5 rounded hover:bg-ink-100 " +
                  (isCurrent ? "bg-accent-subtle text-accent-ink font-medium" : "text-ink-700")
                }
              >
                <span
                  className={
                    "inline-flex items-center justify-center w-5 h-5 rounded-full text-xs " +
                    (isDone
                      ? "bg-accent text-white"
                      : "border border-ink-300 text-ink-500")
                  }
                >
                  {isDone ? "✓" : l.order}
                </span>
                <span className="flex-1">{l.title}</span>
                <span className="text-xs text-ink-400">{l.estimated_minutes}m</span>
              </Link>
            </li>
          );
        })}
      </ol>
    </aside>
  );
}

export function CoursePlayerForCurrent() {
  const { slug, order } = useParams<{ slug: string; order?: string }>();
  if (!slug) return null;
  return <CoursePlayer slug={slug} lessons={[]} currentOrder={order ? Number(order) : undefined} />;
}
