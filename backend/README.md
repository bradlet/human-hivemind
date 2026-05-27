# Hivemind Backend

FastAPI service that backs the Human Hivemind content platform. Subjects
(self-contained mini-courses) are stored as files in object storage, indexed in
Postgres for query, and mutated through a small validation/write pipeline.

- **Source of truth:** content storage (local filesystem in dev, GCS in prod).
- **Index:** Postgres. Rebuildable from storage at any time via `hivemind reindex`.
- **AI side:** each subject can have a regenerated AI-friendly representation
  (`agent.md`, `facts.yaml`, `glossary.yaml`) served from `/api/subjects/{slug}/ai/*`.

---

## Architecture

```
              ┌─────────────┐
   client ──▶ │  api/       │   FastAPI routers (read + write)
              └──┬──────────┘
                 │
                 │ writes
                 ▼
              ┌─────────────┐
              │ pipeline/   │   load_existing → validate_schema
              │             │   → validate_references → check_authorship
              │             │   → moderate (stub) → write_to_storage
              │             │   → update_index → regenerate_ai (stub)
              │             │   → audit_log
              └──┬─────┬────┘
                 │     │
        reads    ▼     ▼   reads/writes
         ┌──────────┐ ┌────────────────┐
         │ services/│ │ storage/       │   LocalStorage / GCSStorage
         │  db_sync │ │  base/local/gcs│
         │  index_  │ └────────────────┘
         │   sync   │
         │ content_io│
         └────┬─────┘
              │
              ▼
         ┌──────────┐
         │   db/    │   SQLAlchemy ORM, Alembic migrations
         └──────────┘
```

**Layer responsibilities:**

| Layer | Purpose |
| --- | --- |
| `api/` | FastAPI routers + DTO schemas. Read endpoints query the index; write endpoints construct a `MutationContext` and run the pipeline. No business logic. |
| `pipeline/` | Ordered, async steps that validate and apply a single subject mutation. Each step is independent and may raise `PipelineRejected` to abort. |
| `services/` | Storage↔domain serialization (`content_io`), index queries (`subject_service`), index rebuild (`index_sync`), shared DB upsert (`db_sync`). |
| `storage/` | Abstract `StorageBackend` + local filesystem and GCS implementations. Path normalization and versioning live here. |
| `db/` | SQLAlchemy models, engine, session factory. |
| `models/` | Pydantic domain models (`SubjectState`, `SubjectManifest`, `DomainTree`, `User`, AI schemas) — the contract the pipeline operates on. |

---

## Directory layout

```
backend/
├── alembic/                 # DB migrations
│   ├── env.py
│   └── versions/0001_initial.py
├── alembic.ini
├── pyproject.toml           # deps, ruff/mypy/pytest config
├── src/hivemind/
│   ├── main.py              # FastAPI app factory, lifespan (migrations + seed)
│   ├── cli.py               # `hivemind` Typer CLI
│   ├── config.py            # pydantic-settings (env-driven Settings)
│   ├── logging_setup.py     # structlog
│   ├── api/                 # FastAPI routers + DTO schemas
│   ├── db/                  # SQLAlchemy models + session
│   ├── models/              # Pydantic domain models + shared validators
│   ├── services/            # content_io, subject_service, index_sync, db_sync
│   ├── storage/             # base, local, gcs, factory
│   └── pipeline/            # context, runner, pipelines, steps/
└── tests/                   # pytest + pytest-asyncio
```

---

## API reference

All routes are prefixed with `/api`. Endpoints requiring a logged-in user are
marked **auth**; everything else is public.

### Health

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Liveness probe. Returns `{ "status": "ok" }`. |

### Domains (`api/domains.py`)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/domains` | Full domain tree (taxonomy). |

### Subjects — read (`api/subjects.py`)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/subjects` | List subjects. Query: `domain`, `search`, `author_id`, `sort` (`title`/`updated_at`/`estimated_hours`/`difficulty`), `limit`. |
| GET | `/api/subjects/{slug}` | Full subject (manifest + overview + lessons + references). |
| GET | `/api/subjects/{slug}/lessons` | Lesson summaries (no body). |
| GET | `/api/subjects/{slug}/lessons/{order}` | Single lesson. |
| GET | `/api/subjects/{slug}/raw.md` | Concatenated raw markdown — AI-friendly blob. |
| GET | `/api/subjects/{slug}/prereqs` | Transitive prerequisite DAG (Postgres recursive CTE). |
| GET | `/api/subjects/{slug}/dependents` | Subjects that list `{slug}` as a direct prerequisite. |
| GET | `/api/subjects/{slug}/history` | Version list per file in the subject directory. |

### Subjects — write (`api/write_subjects.py`) — **auth**

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/subjects` | Create a new subject. |
| PUT | `/api/subjects/{slug}` | Update manifest and/or overview. |
| POST | `/api/subjects/{slug}/lessons` | Create a lesson. |
| PUT | `/api/subjects/{slug}/lessons/{order}` | Update a lesson (URL `order` must match frontmatter). |
| POST | `/api/subjects/{slug}/fork` | Fork to a new slug. |
| POST | `/api/subjects/{slug}/restore?version_id=…` | Restore manifest from a prior storage version. |

### AI (`api/ai.py`)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/subjects/{slug}/ai` | Full AI representation (may be stale; check `is_stale`). |
| GET | `/api/subjects/{slug}/ai.md` | Agent markdown (404 if not yet generated). |
| GET | `/api/subjects/{slug}/ai/facts` | Formulas, theorems, numeric facts. |
| GET | `/api/subjects/{slug}/ai/glossary` | Glossary terms. |

### Auth (`api/auth.py`)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/auth/google` | Start Google OAuth. |
| GET | `/api/auth/google/callback` | OAuth callback; sets session cookie. |
| POST | `/api/auth/dev-login` | **local only.** Sign in as an arbitrary email. |
| GET | `/api/auth/me` | Current user — **auth**. |
| POST | `/api/auth/logout` | Clear session. |

Errors:

- `PipelineRejected` → 400/401/403 JSON `{ "detail", "step" }`.
- Validation `ValueError` → 422.

---

## Data model

Eight tables (see `db/models.py`, schema in `alembic/versions/0001_initial.py`):

- `users` — Google sub + profile.
- `domains` — taxonomy tree (`parent_slug` self-FK).
- `subjects` — core row indexed from storage; tracks `version`, `forked_from_*`.
- `subject_authors` (join) — `subject_id` ↔ `user_id` with role.
- `subject_domains` (join) — `subject_id` ↔ `domain_slug`.
- `subject_prerequisites` (join) — `subject_id` ↔ `prereq_slug`, ordered.
- `lessons` — `(subject_id, order)` unique; `learning_objectives` JSON.
- `edit_events` — append-only audit log of every mutation (accepted or rejected).

Subjects authored by users that aren't in the `users` table (e.g. seed
content) are still indexed; the author join row is just skipped for them.

---

## Storage layout

```
domains.yaml
subjects/
└── {slug}/
    ├── subject.yaml          # manifest
    ├── overview.md
    ├── lessons/
    │   └── NN-kebab-name.md  # YAML frontmatter + body
    ├── exercises/*.md        # optional
    ├── references.md         # optional
    └── ai/
        ├── agent.md          # regenerated
        ├── facts.yaml        # regenerated
        ├── glossary.yaml     # regenerated
        └── meta.yaml         # regenerated_from_human_version, model, etc.
```

Lesson filename regex: `^\d+-[a-z0-9-]+\.md$`. The leading number must match
`frontmatter.order`.

`LocalStorage` simulates GCS object versioning by stashing prior writes under
`<root>/.versions/<path>/<mtime_ns>`. GCS uses native object versioning;
bucket versioning must be enabled.

---

## Mutation pipeline

Defined in `pipeline/pipelines.py`. Steps run in order; each is async and may
raise `PipelineRejected(step, reason, status_code)` to abort.

| # | Step | What it does |
| - | --- | --- |
| 1 | `load_existing` | Load current `SubjectState` from storage (or `None` for CREATE). |
| 2 | `validate_schema` | Build the proposed `SubjectState` for this operation; pydantic-validate; bump `version`. |
| 3 | `validate_references` | Verify every domain and prerequisite slug exists in the DB. |
| 4 | `check_authorship` | CREATE/FORK always allowed; edits require `actor.id` in `existing.manifest.authors`. |
| 5 | `moderate` | **Stub.** Placeholder for safety/diff review. |
| 6 | `write_to_storage` | Serialize and write the proposed state. For FORK, copies the src tree first. |
| 7 | `update_index` | Upsert Postgres rows via `services.db_sync.upsert_subject_state`. |
| 8 | `regenerate_ai_representation` | **Stub.** Placeholder for LLM summary regen. |
| 9 | `audit_log` | Append an `edit_events` row with the recorded step-by-step audit. |

---

## Configuration

All settings come from env vars or `.env` (see `.env.example`). Loaded via
`config.Settings`:

| Var | Default | Notes |
| --- | --- | --- |
| `HIVEMIND_ENV` | `local` | `local` enables CORS and `/api/auth/dev-login`. |
| `HIVEMIND_HOST` / `HIVEMIND_PORT` | `0.0.0.0` / `8080` | |
| `HIVEMIND_LOG_LEVEL` | `INFO` | |
| `STORAGE_BACKEND` | `local` | `local` or `gcs`. |
| `HIVEMIND_LOCAL_CONTENT_ROOT` | `./content` | Used by `LocalStorage`. |
| `HIVEMIND_GCS_BUCKET` / `HIVEMIND_GCS_PREFIX` | — | Used by `GCSStorage`. |
| `DATABASE_URL` | `postgresql+psycopg://hivemind:hivemind@localhost:5432/hivemind` | |
| `GOOGLE_OAUTH_CLIENT_ID` / `_SECRET` / `_REDIRECT_URL` | — | OAuth disabled until id+secret are set. |
| `SESSION_SECRET` | `dev-secret-change-me` | **Replace in prod.** |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS allowlist in `local` mode. |

---

## Running locally

### Docker compose (recommended)

```bash
docker compose up
```

Spins up Postgres, the backend (with hot reload), and the Vite frontend. The
backend runs migrations and seeds the index on first boot.

### Without Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Make sure Postgres is reachable at DATABASE_URL, then:
hivemind run               # or: uvicorn hivemind.main:app --reload
```

---

## CLI

The `hivemind` script (installed by `pip install -e .`) wraps Typer:

```bash
hivemind run [--host 0.0.0.0] [--port 8080]
# Boot the FastAPI app via uvicorn.

hivemind reindex
# Drop and rebuild the Postgres index from content storage. Safe to run any
# time; needed when storage was modified outside the app (e.g. you edited
# content/ files by hand).
```

---

## Alembic migrations

Files live under `backend/alembic/`. Config is `backend/alembic.ini`. The
`env.py` script imports `Settings` and `Base.metadata`, so the migration URL
always tracks `DATABASE_URL` and `target_metadata` always tracks the ORM.

### Automatic application

On every API boot, `main.py:lifespan` calls `_run_migrations(settings)` which
is just:

```python
command.upgrade(cfg, "head")
```

If the upgrade fails the lifespan re-raises and the app fails to start —
migrations are a startup precondition, not best-effort.

### Authoring a new migration

```bash
cd backend
alembic revision --autogenerate -m "add field x to subjects"
```

- Requires `DATABASE_URL` to point at a reachable DB whose current schema
  matches the previous head — autogenerate compares ORM `Base.metadata`
  against the live DB.
- **Always review the generated file.** Autogenerate misses: server defaults,
  enum value renames, check constraints, column type changes that round-trip
  to the same SQL type. Hand-edit the upgrade/downgrade as needed.
- Name the file `NNNN_short_message.py` (`0002_…`, `0003_…`) matching the
  existing convention.
- Write a real `downgrade()` if the change is reversible — leave a clear
  comment if it isn't.

### Applying manually

```bash
cd backend
alembic upgrade head        # apply everything
alembic upgrade +1          # one step forward
alembic upgrade <rev_id>    # to a specific revision
```

### Rolling back

```bash
alembic downgrade -1        # one step back
alembic downgrade <rev_id>  # to a specific revision
alembic downgrade base      # nuke the schema (DESTRUCTIVE)
```

### Inspecting state

```bash
alembic current             # which revision is the DB at?
alembic history             # full timeline
alembic heads               # there should only ever be one head
```

### Offline SQL

```bash
alembic upgrade head --sql > migration.sql
```

Useful when a DBA applies migrations by hand or for review.

### Gotchas

- **Multiple heads?** Resolve with `alembic merge -m "merge X and Y" <head1> <head2>`.
- **Python enum changes** (e.g. adding a value to `Difficulty`) aren't picked
  up by autogenerate — write the migration manually.
- **Running migrations in a one-off shell** — make sure `DATABASE_URL` is set
  in your shell env, not just in a `.env` you forgot to source. `env.py`
  reads from `Settings`, which reads from the env.
- **Don't edit a migration that's been applied to a shared DB.** Add a new one.

---

## Testing

```bash
cd backend
pytest                       # full suite (uses in-memory SQLite by default)
pytest -k subject            # filter by name
pytest --cov=hivemind        # with coverage
```

Fixtures live in `tests/conftest.py`: `temp_content` (tmp_path), `storage`
(LocalStorage over that path), `db` (SQLite session).

A few tests use Postgres-only features (recursive CTE in `transitive_prereqs`).
They auto-skip on SQLite. To run them against a real Postgres:

```bash
TEST_DATABASE_URL=postgresql+psycopg://hivemind:hivemind@localhost:5432/hivemind_test pytest
```

`asyncio_mode = "auto"` is set in `pyproject.toml`, so async tests Just Work.

---

## Lint and types

```bash
cd backend
ruff check src tests
ruff format src tests
mypy src
```

Ruff config and mypy config are in `pyproject.toml`.

---

## Manual API interaction

A dev session (local mode, OAuth disabled):

```bash
# Liveness
curl -s http://localhost:8080/api/health

# Browse
curl -s http://localhost:8080/api/domains | jq
curl -s 'http://localhost:8080/api/subjects?sort=title&limit=10' | jq

# Detail
curl -s http://localhost:8080/api/subjects/<slug> | jq

# Dev login (local only) — store cookies for subsequent writes
curl -s -c cookies.txt -X POST \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","name":"Me"}' \
  http://localhost:8080/api/auth/dev-login

# Confirm session
curl -s -b cookies.txt http://localhost:8080/api/auth/me | jq

# Create a subject (see CreateSubjectIn in api/schemas.py for full shape)
curl -s -b cookies.txt -X POST \
  -H 'Content-Type: application/json' \
  -d @new-subject.json \
  http://localhost:8080/api/subjects | jq
```
