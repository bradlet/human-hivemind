const KEY = (slug: string) => `hivemind:progress:${slug}`;

export function loadProgress(slug: string): Set<number> {
  if (typeof window === "undefined") return new Set();
  try {
    const raw = localStorage.getItem(KEY(slug));
    if (!raw) return new Set();
    return new Set(JSON.parse(raw));
  } catch {
    return new Set();
  }
}

export function setLessonComplete(slug: string, order: number, complete: boolean): void {
  const set = loadProgress(slug);
  if (complete) set.add(order);
  else set.delete(order);
  localStorage.setItem(KEY(slug), JSON.stringify([...set]));
}
