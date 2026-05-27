"""`hivemind` CLI.

  hivemind reindex
        Rebuild the Postgres index from content storage.

  hivemind run [--host 0.0.0.0] [--port 8080]
        Boot the app with uvicorn (mostly for one-off launches; prod uses the
        Docker entrypoint directly).
"""
from __future__ import annotations

import typer

from hivemind.config import get_settings
from hivemind.db.session import SessionLocal, init_engine
from hivemind.logging_setup import configure_logging, get_logger
from hivemind.services import index_sync
from hivemind.storage import build_storage

app = typer.Typer(help="Human Hivemind CLI")
log = get_logger("hivemind.cli")


@app.command()
def reindex() -> None:
    """Rebuild the Postgres index from content storage."""
    settings = get_settings()
    configure_logging(settings.log_level)
    init_engine(settings.database_url)
    storage = build_storage(settings)
    with SessionLocal() as db:
        report = index_sync.reindex(db, storage)
    typer.echo(
        f"Reindex complete. domains={report.domains} subjects={report.subjects} "
        f"lessons={report.lessons} skipped={len(report.skipped)}"
    )
    for slug, reason in report.skipped:
        typer.echo(f"  skipped {slug}: {reason}")


@app.command()
def run(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Launch the FastAPI app via uvicorn."""
    import uvicorn

    uvicorn.run("hivemind.main:app", host=host, port=port, factory=False)


if __name__ == "__main__":
    app()
