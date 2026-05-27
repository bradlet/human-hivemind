# AGENTS.md

For agents working in this repo. Read this first.

## Mental model

- **Two stores, one source of truth.** Content storage (GCS prod, local FS dev) holds markdown bytes — this is the source of truth. Postgres is a *rebuildable* index of metadata for queries. If they diverge, run `python -m hivemind.cli reindex` to rebuild Postgres from storage. Never the other way.
- **Dual representation per subject.** `subjects/{slug}/*` is human-edited. `subjects/{slug}/ai/*` is pipeline-generated (currently stubbed; seed subjects ship hand-written `ai/`). Humans never edit `ai/`; the regen step owns it.
- **One pipeline for every mutation.** Create, update, fork, restore, add lesson — all go through `pipeline/runner.py:run_pipeline` with a step list from `pipeline/pipelines.py`. New mutation logic = new step file, not a new code path.
- **Schemas are the contract.** `models/subject.py` and `models/domain.py` enforce course structure (required ordered lessons, required learning objectives, required prereq slugs are valid). If you weaken validation, you weaken the platform's identity.

## Where things live (only the non-obvious bits)

| What | Where |
|---|---|
| File layout of a subject (manifest path, lesson path, AI prefix) | `backend/src/hivemind/services/content_io.py` |
| Serialize / load a `SubjectState` from storage | `services/content_io.py` (`load_subject_state`, `dump_subject_state`) |
| Pipeline steps (one file each) | `backend/src/hivemind/pipeline/steps/` |
| Per-operation step list | `pipeline/pipelines.py` (default is used by all ops in v1) |
| Recursive prereq CTE | `services/subject_service.py::transitive_prereqs` (Postgres-only) |
| Storage selector | `storage/factory.py` (env-driven, no GCS emulator) |
| Settings | `config.py` (pydantic-settings, env-driven) |
| FastAPI app + startup migrations + auto-seed | `main.py` |
| CLI (`hivemind reindex`, `hivemind run`) | `cli.py` |
| Frontend API client | `frontend/src/lib/api.ts` |

## Conventions

- **Python 3.12+.** `from __future__ import annotations` at the top of every module. Strict type hints. Ruff lints `src/`; rules in `backend/pyproject.toml`.
- **Tests live in `backend/tests/`** and use SQLite, not Postgres. The one Postgres-specific feature (recursive CTE in `transitive_prereqs`) is not unit-tested for that reason; integration-test it manually via `docker compose`.
- **Frontend uses SWR for all server state.** Don't reach for global state libs (and don't add TanStack Query back — SWR was chosen because this is a read-heavy app with rare, isolated mutations). Use array keys like `["subject", slug]`; pass `null` as the key to disable a fetch. Invalidate with `useSWRConfig().mutate(key)`. Global retry/backoff lives in `frontend/src/main.tsx`. Routes are in `frontend/src/routes/`; reusable bits in `frontend/src/components/`.
- **Slugs are lowercase kebab-case.** Regex enforced in `models/subject.py::SLUG_RE` and `models/domain.py::SLUG_RE`. Never accept arbitrary user input as a slug without validating.
- **Markdown bodies live in storage, not Postgres.** If you find yourself adding a `body` column to a SQLAlchemy model, stop.

## When making changes

### Adding a new mutation operation

1. Add a variant to `pipeline/context.py::MutationOperation`.
2. Add a new pipeline step file under `pipeline/steps/` if needed, and export it from `pipeline/steps/__init__.py`.
3. Add or update a per-operation step list in `pipeline/pipelines.py::pipeline_for_operation`.
4. Add the API route under `api/write_subjects.py` (or its own router); route the request through `run_pipeline`.
5. Write a test in `backend/tests/test_pipeline.py`.

### Adding a new pipeline step

Step signature: `async def step(ctx: MutationContext) -> MutationContext`. Raise `PipelineRejected(step, reason, status_code=…)` to abort. Append to `ctx.audit` via `ctx.record(step_name, **fields)` for observability. Place between the existing steps in `DEFAULT_PIPELINE` where it semantically belongs (validation early, persistence late).

### Adding a field to a subject manifest

1. Update `models/subject.py::SubjectManifest`.
2. Update the Alembic migration: add a new migration under `backend/alembic/versions/` (don't edit `0001_initial.py`).
3. Update the `SubjectRow` SQLAlchemy model in `db/models.py` and the upsert logic in `pipeline/steps/update_index.py` and `services/index_sync.py`.
4. Update the API DTO in `api/schemas.py::SubjectDetailOut`.
5. Update seed content under `content/subjects/*/subject.yaml` so existing subjects validate.
6. Add a schema test in `backend/tests/test_schemas.py`.

### Replacing a stub step (moderate / regenerate_ai_representation)

The interface is intentionally stable. Edit only the file at `pipeline/steps/{moderate,regenerate_ai_representation}.py`. No changes elsewhere should be required. If your replacement is slow (LLM call), move it to a background task before merging — don't block the user-facing write.

### Editing a seed subject

Edit files under `content/subjects/{slug}/` directly. The startup hook re-seeds Postgres only when the index is empty; bump versions by hand or run `hivemind reindex` to push changes through.

## Running things

```bash
# Local dev (all three services)
docker compose up

# Backend tests
.venv/bin/pytest backend/tests

# Backend lint
.venv/bin/ruff check backend/src

# Frontend build
cd frontend && npm run build

# Frontend tests
cd frontend && npm test

# Reindex Postgres from content storage
docker compose exec backend python -m hivemind.cli reindex
```

## Stuff to avoid

- **Don't add a GCS emulator** — local dev uses `LocalStorage` against `./content/`. Single env-driven selector.
- **Don't mix read and write paths.** Writes go through the pipeline. Reads use `services/subject_service.py` helpers + `services/content_io.py`.
- **Don't store user-editable content in Postgres.** It's an index. The bytes belong in storage.
- **Don't fetch a subject from storage on every API call when Postgres has the answer.** Use Postgres for filter/list/prereq/domain queries; only hit storage when you need a markdown body.
- **Don't bypass `MutationContext.actor` for authorship checks.** `check_authorship` is the only place that decides who can edit what.
