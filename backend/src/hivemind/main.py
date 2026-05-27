"""FastAPI app factory.

Wires up:
  - Session middleware (itsdangerous-signed cookies, httpOnly)
  - CORS for the Vite dev origin in local mode
  - All API routers under /api
  - Static-file serving for the React build (in production)
  - Exception handlers that translate PipelineRejected into HTTP responses
  - A startup hook that runs Alembic migrations and seeds the index if needed
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware

from hivemind.api import ai, auth, domains, images, subjects, write_subjects
from hivemind.api.deps import get_storage
from hivemind.config import Settings, get_settings
from hivemind.db.models import SubjectRow
from hivemind.db.session import SessionLocal, init_engine
from hivemind.logging_setup import configure_logging, get_logger
from hivemind.pipeline.context import PipelineRejected
from hivemind.services import index_sync

log = get_logger("hivemind.main")


def _run_migrations(settings: Settings) -> None:
    here = Path(__file__).resolve().parent.parent.parent
    cfg = Config(str(here / "alembic.ini"))
    cfg.set_main_option("script_location", str(here / "alembic"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, "head")


def _seed_index_if_empty(settings: Settings) -> None:
    with SessionLocal() as db:
        existing = db.execute(select(SubjectRow.id).limit(1)).first()
        if existing is not None:
            log.info("startup.index.populated")
            return
        storage = get_storage(settings)
        log.info("startup.index.seeding")
        index_sync.reindex(db, storage)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    init_engine(settings.database_url)
    try:
        _run_migrations(settings)
    except Exception as exc:
        log.error("startup.migrations_failed", error=str(exc))
        raise
    try:
        _seed_index_if_empty(settings)
    except Exception as exc:
        log.warning("startup.seed_failed", error=str(exc))
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    s = settings or get_settings()
    app = FastAPI(
        title="Human Hivemind",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=s.session_secret,
        https_only=not s.is_local,
        same_site="lax",
    )

    allowed_origins = [s.frontend_origin] if s.is_local else []
    if allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.exception_handler(PipelineRejected)
    async def _pipeline_rejected_handler(
        request: Request, exc: PipelineRejected
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.reason, "step": exc.step},
        )

    @app.exception_handler(ValueError)
    async def _value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    app.include_router(domains.router, prefix="/api")
    app.include_router(subjects.router, prefix="/api")
    app.include_router(ai.router, prefix="/api")
    app.include_router(write_subjects.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(images.router, prefix="/api")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": app.version}

    dist_dir = Path(__file__).resolve().parent / "static"
    if dist_dir.exists():
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="ui")

    return app


app = create_app()
