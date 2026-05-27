# Human Hivemind

**A free, open-source platform where anyone can learn anything — and where every course doubles as structured knowledge for AI.**

Wikipedia gave the internet a place to share *facts*. Coursera and Khan Academy gave it a place to take *courses*. Neither did both, and neither was designed for the world we're now in, where AI assistants are how millions of people actually learn.

Human Hivemind is trying to be the bridge:

- **For humans**, it's a place to learn and teach. Every topic — from linear algebra to deep neural networks to literary analysis — is organized as a structured course with an overview, ordered lessons, explicit learning objectives, and a graph of prerequisites that guides you to the right starting point. Anyone can author a subject. If you disagree with how someone else has explained a topic, you fork it and write your own version, and the community decides which version best serves learners.
- **For AI**, it's an interoperable knowledge repository. Every subject is stored *twice*: a rich human representation (the lessons humans read and edit), and a terse AI representation (an `AGENTS.md`-style brief plus structured facts and a glossary). The AI representation is automatically regenerated from the human source — think of it as compiled output. AI tutors, agents, and assistants can pull the AI version of any subject in a single request and immediately have a token-efficient, structured view of the material. They can then tutor humans on those same courses, or use the knowledge to do downstream work.

The flywheel: humans teach humans → AI distills what humans wrote → AI helps the next humans learn it → those humans contribute back. Knowledge compounds in both directions.

## What makes it different from a wiki

The file format itself enforces course structure. Every subject must have:

- a manifest (`subject.yaml`) declaring its domains, prerequisites, authors, difficulty, and estimated hours
- an overview that answers "what will I learn?"
- at least one lesson, with frontmatter declaring its order, title, estimated time, and learning objectives

If those things aren't there, the content doesn't validate, and the platform refuses to publish it. This is the difference between a wiki article and a course.

## Architecture at a glance

```
   ┌──────────────┐                  ┌──────────────────────┐
   │   Browser    │ ───▶ React UI ─▶ │                      │
   └──────────────┘                  │   FastAPI + Uvicorn  │
                                     │                      │
   ┌──────────────┐                  │  ┌────────────────┐  │
   │  AI client   │ ───▶ /api/...ai ─▶  │   Mutation     │  │
   │  (LLM/agent) │                  │  │   Pipeline     │  │
   └──────────────┘                  │  └───────┬────────┘  │
                                     └──────────┼───────────┘
                                                │
                       ┌────────────────────────┼────────────────────────┐
                       ▼                                                 ▼
              ┌─────────────────┐                            ┌────────────────────┐
              │  Postgres index │                            │  Content storage   │
              │ (queryable      │                            │  (GCS or local FS) │
              │  metadata only) │                            │  source of truth   │
              └─────────────────┘                            └────────────────────┘
```

- **Content storage** is the source of truth. GCS in production (with object versioning for free per-file history) or the local filesystem in dev. Markdown bytes live here.
- **Postgres** holds a fully rebuildable index: subjects, domains, prerequisites, authors, lessons metadata, audit events. Reads use Postgres for fast queries (domain filters, prereq graphs, search); markdown bodies are fetched from content storage.
- **Mutation pipeline** is a composable list of small async steps that every create / update / fork / restore flows through:

  ```
  load_existing → validate_schema → validate_references → check_authorship
  → moderate (v1 stub) → write_to_storage → update_index
  → regenerate_ai_representation (v1 stub) → audit_log
  ```

  The `moderate` and `regenerate_ai_representation` steps are intentional stubs in v1 — they log a `todo: …` line and pass through. Replacing either with real logic (AI fact-checking, CSAM screening, LLM-driven regeneration of the AI representation) is a one-file change that requires nothing else in the pipeline to move.

- **Dual content representation**:
  - *Human side* (`subjects/{slug}/subject.yaml`, `overview.md`, `lessons/`) — what people read and edit.
  - *AI side* (`subjects/{slug}/ai/agent.md`, `facts.yaml`, `glossary.yaml`, `meta.yaml`) — what AI clients pull. Regenerated from the human side by the pipeline; never user-edited.

## Repo layout

| Path | What's in it |
|---|---|
| [`backend/`](backend/) | FastAPI app, Pydantic models, mutation pipeline, SQLAlchemy + Alembic |
| `backend/src/hivemind/storage/` | `LocalStorage` (dev) and `GCSStorage` (prod) implementations of one tiny `StorageBackend` interface |
| `backend/src/hivemind/pipeline/steps/` | One file per pipeline step — clearest place to start when changing or extending mutation behavior |
| `backend/src/hivemind/api/` | FastAPI routers for human-side reads, AI-side reads, writes (through the pipeline), and auth |
| [`frontend/`](frontend/) | React + Vite + TypeScript course player, prereq graph, CodeMirror editor |
| [`content/`](content/) | Seed markdown content — also the local-fs storage root in dev |
| [`Dockerfile`](Dockerfile) | Single production image; multi-stage (node builds frontend → python serves API + static dist) |
| [`docker-compose.yml`](docker-compose.yml) | Local dev: `postgres` + `backend` (uvicorn --reload) + `frontend` (Vite HMR) |
| [`AGENTS.md`](AGENTS.md) | Conventions for AI agents working in this repo |

## API surface

Read endpoints (no auth required):

- `GET /api/domains` — domain tree
- `GET /api/subjects` — filterable / sortable subject list
- `GET /api/subjects/{slug}` — full subject (manifest + lessons inline)
- `GET /api/subjects/{slug}/lessons/{order}` — single lesson
- `GET /api/subjects/{slug}/prereqs` — transitive prereq DAG (recursive CTE)
- `GET /api/subjects/{slug}/dependents` — reverse prereq lookup
- `GET /api/subjects/{slug}/raw.md` — concatenated human markdown (escape hatch for agents)
- `GET /api/subjects/{slug}/history` — object-versioning history per file

AI-side reads (terse, token-efficient — intended for LLM clients):

- `GET /api/subjects/{slug}/ai` — `agent.md` + facts + glossary + staleness metadata
- `GET /api/subjects/{slug}/ai.md` — just the agent doc, as plain markdown
- `GET /api/subjects/{slug}/ai/facts` — structured key facts
- `GET /api/subjects/{slug}/ai/glossary` — term → definition

Write endpoints (auth required, all routed through the mutation pipeline):

- `POST /api/subjects` — create a new subject (creator becomes sole author)
- `PUT /api/subjects/{slug}` — update manifest / overview (authors only)
- `PUT /api/subjects/{slug}/lessons/{order}` — update a lesson (authors only)
- `POST /api/subjects/{slug}/lessons` — add a lesson (authors only)
- `POST /api/subjects/{slug}/fork` — copy a subject under a new slug, you become the sole author
- `POST /api/subjects/{slug}/restore?version_id=…` — restore a prior version of the manifest (authors only)

## Local development

```bash
cp .env.example .env
docker compose up
```

Three services start:

- **postgres** (16-alpine) on `localhost:5432`
- **backend** (FastAPI + Uvicorn with `--reload`) on `localhost:8080`
- **frontend** (Vite dev with HMR, proxies `/api` to backend) on `localhost:5173`

On first start, the backend runs Alembic migrations and seeds Postgres by reindexing the markdown in `./content/`.

To rebuild the Postgres index from content storage at any time:

```bash
docker compose exec backend python -m hivemind.cli reindex
```

There's a `dev` button in the header that lets you sign in with any email locally (skips Google OAuth in dev mode). Sign in, browse to a subject, click "Edit", and the changes flow through the same mutation pipeline that production uses.

## Production

A single multi-stage [`Dockerfile`](Dockerfile) builds the frontend with Node and serves it alongside the API from one Python Uvicorn process. Provide a Postgres `DATABASE_URL` (any managed Postgres works — Cloud SQL, Neon, RDS, …), set `STORAGE_BACKEND=gcs`, point `HIVEMIND_GCS_BUCKET` at a bucket with **object versioning enabled**, and configure Google OAuth credentials. That's it.

```bash
docker build -t hivemind .
docker run -p 8080:8080 --env-file .env hivemind
```

## What's deliberately deferred

- **Moderation** — the `moderate` pipeline step is a logging stub; full design is in [GitHub issue #1](https://github.com/bradlet/human-hivemind/issues/1).
- **The LLM call inside `regenerate_ai_representation`** — also a stub. Seed subjects ship with hand-written AI representations that double as the prompt's target output spec.
- **Wikipedia-style anonymous edits** — v1 is authors-only with fork-to-edit. Cleaner moderation story.
- **Merge-back from forks** — forks are siblings, not branches.
- **Images and video embeds** — v1 is text-only.
- **Full-text search** — basic title / domain filtering only.

## Contributing

The two highest-leverage places to start:

1. Author or improve a seed subject under [`content/subjects/`](content/subjects/). The schema is enforced at load time, so a malformed subject won't break anything — you'll just get a validation error pointing at the problem.
2. Replace one of the stub pipeline steps in [`backend/src/hivemind/pipeline/steps/`](backend/src/hivemind/pipeline/steps/). Each step is its own file; the contract is "take a `MutationContext`, return a `MutationContext`, or raise `PipelineRejected`."

If you're an AI agent working on this repo, read [`AGENTS.md`](AGENTS.md) first.
