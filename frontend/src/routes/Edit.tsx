import { Link, useNavigate, useParams } from "react-router-dom";
import useSWR, { useSWRConfig } from "swr";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import LessonEditor from "../components/LessonEditor";
import LessonViewer from "../components/LessonViewer";

export default function Edit() {
  const { slug, order } = useParams<{ slug: string; order?: string }>();
  const navigate = useNavigate();
  const { mutate } = useSWRConfig();

  const me = useSWR("me", api.me, { shouldRetryOnError: false });
  const subject = useSWR(slug ? ["subject", slug] : null, () => api.subject(slug!));

  const editingLessonOrder = order ? Number(order) : undefined;

  const [lessonBody, setLessonBody] = useState("");
  const [lessonTitle, setLessonTitle] = useState("");
  const [lessonMinutes, setLessonMinutes] = useState(20);
  const [lessonObjectives, setLessonObjectives] = useState<string[]>([""]);
  const [overview, setOverview] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!subject.data) return;
    setOverview(subject.data.overview);
    if (editingLessonOrder != null) {
      const lesson = subject.data.lessons.find((l) => l.order === editingLessonOrder);
      if (lesson) {
        setLessonBody(lesson.body);
        setLessonTitle(lesson.title);
        setLessonMinutes(lesson.estimated_minutes);
        setLessonObjectives(lesson.learning_objectives);
      }
    }
  }, [subject.data, editingLessonOrder]);

  if (subject.isLoading) {
    return (
      <div className="dark:bg-ink-950 min-h-screen">
        <div className="max-w-6xl mx-auto px-4 py-10 text-ink-400">Loading…</div>
      </div>
    );
  }
  if (!subject.data) {
    return (
      <div className="dark:bg-ink-950 min-h-screen">
        <div className="max-w-6xl mx-auto px-4 py-10 text-ink-900 dark:text-ink-100">
          Subject not found.
        </div>
      </div>
    );
  }
  const s = subject.data;
  const isAuthor = !!me.data && s.authors.some((a) => a.id === me.data!.id);
  if (!isAuthor) {
    return (
      <div className="dark:bg-ink-950 min-h-screen">
        <div className="max-w-6xl mx-auto px-4 py-10">
          <h1 className="text-2xl font-semibold mb-2 text-ink-900 dark:text-ink-100">
            Not authorized
          </h1>
          <p className="text-ink-700 dark:text-ink-300 mb-4">
            Only the listed authors of <code>{s.slug}</code> can edit this subject.
            You can <em>fork</em> it to make your own version.
          </p>
          <Link to={`/s/${s.slug}`} className="text-accent hover:text-violet-300">
            Back to subject
          </Link>
        </div>
      </div>
    );
  }

  const onSaveLesson = async () => {
    if (editingLessonOrder == null) return;
    setSaving(true);
    setError(null);
    try {
      const cleanedObjectives = lessonObjectives
        .map((o) => o.trim())
        .filter((o) => o.length > 0);
      if (cleanedObjectives.length === 0) {
        throw new Error("At least one learning objective is required.");
      }
      const original = s.lessons.find((l) => l.order === editingLessonOrder);
      const filename = (original as any)?.filename ?? `${String(editingLessonOrder).padStart(2, "0")}-lesson.md`;
      await api.updateLesson(s.slug, editingLessonOrder, {
        filename,
        frontmatter: {
          order: editingLessonOrder,
          title: lessonTitle,
          estimated_minutes: lessonMinutes,
          learning_objectives: cleanedObjectives,
        },
        body: lessonBody,
      });
      mutate(["subject", s.slug]);
      navigate(`/s/${s.slug}/l/${editingLessonOrder}`);
    } catch (err: any) {
      setError(err.message ?? String(err));
    } finally {
      setSaving(false);
    }
  };

  const onSaveOverview = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.updateSubject(s.slug, {
        manifest: {
          title: s.title,
          domains: s.domains,
          prerequisites: s.prerequisites,
          estimated_hours: s.estimated_hours,
          difficulty: s.difficulty,
          status: s.status,
        },
        overview,
      });
      mutate(["subject", s.slug]);
      navigate(`/s/${s.slug}`);
    } catch (err: any) {
      setError(err.message ?? String(err));
    } finally {
      setSaving(false);
    }
  };

  // NOTE: The CodeMirror editor used in LessonEditor keeps its built-in light theme.
  // Switching it to a dark theme would require swapping its theme extension at runtime
  // (non-trivial), so we intentionally leave it as-is for this pass.
  return (
    <div className="dark:bg-ink-950 min-h-screen">
      <div className="max-w-6xl mx-auto px-4 py-10">
        <div className="text-sm mb-2">
          <Link
            to={`/s/${s.slug}`}
            className="text-accent hover:text-violet-300 transition-colors"
          >
            &larr; {s.title}
          </Link>
        </div>
        <h1 className="text-2xl font-semibold mb-6 text-ink-900 dark:text-ink-100">
          Edit {editingLessonOrder ? `lesson ${editingLessonOrder}` : "subject overview"}
        </h1>

        {error && (
          <div className="bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-700 dark:text-red-300 rounded p-3 mb-4 whitespace-pre-wrap text-sm">
            {error}
          </div>
        )}

        {editingLessonOrder == null ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="text-xs uppercase tracking-wider text-ink-500 dark:text-ink-400 mb-2">
                Overview markdown
              </h3>
              <LessonEditor value={overview} onChange={setOverview} />
              <button
                disabled={saving}
                onClick={onSaveOverview}
                className="mt-4 bg-accent text-white px-4 py-2 rounded hover:bg-accent-ink disabled:opacity-50 glow-accent transition-shadow"
              >
                {saving ? "Saving…" : "Save overview"}
              </button>
            </div>
            <div>
              <h3 className="text-xs uppercase tracking-wider text-ink-500 dark:text-ink-400 mb-2">
                Preview
              </h3>
              <div className="bg-white dark:bg-ink-900/50 border border-ink-200 dark:border-ink-800 rounded p-4 min-h-[60vh]">
                <LessonViewer markdown={overview} />
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <label className="block text-sm">
                  <div className="text-ink-600 dark:text-ink-300 mb-1">Title</div>
                  <input
                    className="border border-ink-300 dark:border-ink-700 dark:bg-ink-800 dark:text-ink-100 dark:placeholder-ink-400 focus:ring-2 focus:ring-accent/40 focus:outline-none rounded px-2 py-1.5 w-full"
                    value={lessonTitle}
                    onChange={(e) => setLessonTitle(e.target.value)}
                  />
                </label>
                <label className="block text-sm">
                  <div className="text-ink-600 dark:text-ink-300 mb-1">Estimated minutes</div>
                  <input
                    type="number"
                    min={1}
                    className="border border-ink-300 dark:border-ink-700 dark:bg-ink-800 dark:text-ink-100 dark:placeholder-ink-400 focus:ring-2 focus:ring-accent/40 focus:outline-none rounded px-2 py-1.5 w-full"
                    value={lessonMinutes}
                    onChange={(e) => setLessonMinutes(Number(e.target.value))}
                  />
                </label>
              </div>
              <div>
                <div className="text-sm text-ink-600 dark:text-ink-300 mb-1">Learning objectives</div>
                {lessonObjectives.map((obj, i) => (
                  <div key={i} className="flex items-center gap-2 mb-1">
                    <input
                      className="border border-ink-300 dark:border-ink-700 dark:bg-ink-800 dark:text-ink-100 dark:placeholder-ink-400 focus:ring-2 focus:ring-accent/40 focus:outline-none rounded px-2 py-1.5 flex-1 text-sm"
                      value={obj}
                      onChange={(e) => {
                        const next = [...lessonObjectives];
                        next[i] = e.target.value;
                        setLessonObjectives(next);
                      }}
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setLessonObjectives(lessonObjectives.filter((_, j) => j !== i))
                      }
                      className="text-ink-500 dark:text-ink-400 hover:text-red-600 dark:hover:text-red-400 text-sm"
                    >
                      remove
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => setLessonObjectives([...lessonObjectives, ""])}
                  className="text-sm text-accent hover:text-violet-300"
                >
                  + add objective
                </button>
              </div>
              <div>
                <div className="text-sm text-ink-600 dark:text-ink-300 mb-1">Body markdown</div>
                <LessonEditor value={lessonBody} onChange={setLessonBody} />
              </div>
              <button
                disabled={saving}
                onClick={onSaveLesson}
                className="bg-accent text-white px-4 py-2 rounded hover:bg-accent-ink disabled:opacity-50 glow-accent transition-shadow"
              >
                {saving ? "Saving…" : "Save lesson"}
              </button>
            </div>
            <div>
              <h3 className="text-xs uppercase tracking-wider text-ink-500 dark:text-ink-400 mb-2">
                Preview
              </h3>
              <div className="bg-white dark:bg-ink-900/50 border border-ink-200 dark:border-ink-800 rounded p-4 min-h-[60vh]">
                <LessonViewer markdown={lessonBody} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
