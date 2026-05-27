export type DomainNode = {
  slug: string;
  title: string;
  children: DomainNode[];
};

export type DomainTree = { domains: DomainNode[] };

export type Author = { id: string; name?: string | null; avatar_url?: string | null };

export type SubjectSummary = {
  slug: string;
  title: string;
  status: string;
  difficulty: string;
  estimated_hours: number;
  version: number;
  updated_at: string;
};

export type LessonSummary = {
  order: number;
  title: string;
  estimated_minutes: number;
  learning_objectives: string[];
};

export type Lesson = LessonSummary & { body: string };

export type SubjectDetail = {
  slug: string;
  title: string;
  domains: string[];
  prerequisites: string[];
  authors: Author[];
  estimated_hours: number;
  difficulty: string;
  status: string;
  version: number;
  forked_from?: { slug: string; version: number } | null;
  overview: string;
  lessons: Lesson[];
  references?: string | null;
};

export type PrereqNode = {
  slug: string;
  title: string;
  depth: number;
  via: string | null;
};

export type Prereqs = { slug: string; nodes: PrereqNode[] };

export type Dependents = { slug: string; dependents: SubjectSummary[] };

export type AIRepresentation = {
  slug: string;
  agent_md: string | null;
  facts: { key_formulas: any[]; key_theorems: any[]; numeric_facts: string[] } | null;
  glossary: { terms: Record<string, string> } | null;
  regenerated_at: string | null;
  regenerated_from_human_version: number | null;
  current_human_version: number;
  is_stale: boolean;
  model: string | null;
};

export type Me = { id: string; email: string; name: string; avatar_url: string | null };

const BASE = "/api";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public step?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    let step: string | undefined;
    try {
      const data = await res.json();
      detail = data.detail ?? detail;
      step = data.step;
    } catch {
      // body wasn't JSON
    }
    throw new ApiError(detail, res.status, step);
  }
  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json() as Promise<T>;
  return res.text() as unknown as Promise<T>;
}

export const api = {
  domains: () => request<DomainTree>("/domains"),
  listSubjects: (params: { domain?: string; search?: string; sort?: string } = {}) => {
    const qs = new URLSearchParams();
    if (params.domain) qs.set("domain", params.domain);
    if (params.search) qs.set("search", params.search);
    if (params.sort) qs.set("sort", params.sort);
    const suffix = qs.toString() ? `?${qs}` : "";
    return request<SubjectSummary[]>(`/subjects${suffix}`);
  },
  subject: (slug: string) => request<SubjectDetail>(`/subjects/${slug}`),
  lesson: (slug: string, order: number) =>
    request<Lesson>(`/subjects/${slug}/lessons/${order}`),
  prereqs: (slug: string) => request<Prereqs>(`/subjects/${slug}/prereqs`),
  dependents: (slug: string) => request<Dependents>(`/subjects/${slug}/dependents`),
  ai: (slug: string) => request<AIRepresentation>(`/subjects/${slug}/ai`),

  me: () => request<Me>("/auth/me"),
  devLogin: (email: string, name?: string) =>
    request<Me>("/auth/dev-login", {
      method: "POST",
      body: JSON.stringify({ email, name }),
    }),
  logout: () => request<{ ok: boolean }>("/auth/logout", { method: "POST" }),

  updateSubject: (
    slug: string,
    body: { manifest: any; overview?: string },
  ) =>
    request<SubjectDetail>(`/subjects/${slug}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  updateLesson: (slug: string, order: number, lesson: any) =>
    request<SubjectDetail>(`/subjects/${slug}/lessons/${order}`, {
      method: "PUT",
      body: JSON.stringify(lesson),
    }),
  createSubject: (body: any) =>
    request<SubjectDetail>("/subjects", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  forkSubject: (slug: string, newSlug: string) =>
    request<SubjectDetail>(`/subjects/${slug}/fork`, {
      method: "POST",
      body: JSON.stringify({ new_slug: newSlug }),
    }),
};

export { ApiError };
