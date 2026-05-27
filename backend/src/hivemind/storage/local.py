"""Local filesystem storage backend (used in dev).

Versioning is approximated by keeping prior writes in a hidden sibling
`.versions/{path}/{timestamp}` tree. Good enough for local dev so that the
history API surface works against this backend; prod uses GCS object versioning
which gives us real version IDs.
"""
from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

from hivemind.storage.base import (
    ObjectVersion,
    StorageBackend,
    StoredObject,
    StoredObjectNotFound,
    normalize_path,
)

VERSIONS_DIRNAME = ".versions"


class LocalStorage(StorageBackend):
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        (self._root / VERSIONS_DIRNAME).mkdir(exist_ok=True)

    def _resolve(self, path: str) -> Path:
        p = normalize_path(path)
        full = (self._root / p).resolve()
        if not str(full).startswith(str(self._root)):
            raise ValueError(f"Storage path escapes root: {path!r}")
        return full

    def _versions_dir(self, path: str) -> Path:
        return self._root / VERSIONS_DIRNAME / normalize_path(path)

    def read(self, path: str, *, version_id: str | None = None) -> StoredObject:
        if version_id is None:
            full = self._resolve(path)
            if not full.exists():
                raise StoredObjectNotFound(path)
            data = full.read_bytes()
            stat = full.stat()
            return StoredObject(
                path=normalize_path(path),
                data=data,
                version_id=str(stat.st_mtime_ns),
                updated_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            )
        versions_dir = self._versions_dir(path)
        candidate = versions_dir / version_id
        if not candidate.exists():
            raise StoredObjectNotFound(f"{path}@{version_id}")
        data = candidate.read_bytes()
        stat = candidate.stat()
        return StoredObject(
            path=normalize_path(path),
            data=data,
            version_id=version_id,
            updated_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
        )

    def write(self, path: str, data: bytes) -> StoredObject:
        full = self._resolve(path)
        full.parent.mkdir(parents=True, exist_ok=True)

        if full.exists():
            existing = full.read_bytes()
            if existing != data:
                versions_dir = self._versions_dir(path)
                versions_dir.mkdir(parents=True, exist_ok=True)
                ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
                (versions_dir / ts).write_bytes(existing)

        full.write_bytes(data)
        stat = full.stat()
        return StoredObject(
            path=normalize_path(path),
            data=data,
            version_id=str(stat.st_mtime_ns),
            updated_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
        )

    def delete(self, path: str) -> None:
        try:
            full = self._resolve(path)
        except ValueError:
            return
        if full.exists():
            full.unlink()

    def exists(self, path: str) -> bool:
        try:
            full = self._resolve(path)
        except ValueError:
            return False
        return full.exists() and full.is_file()

    def list_prefix(self, prefix: str) -> list[str]:
        prefix = normalize_path(prefix)
        full_prefix = (self._root / prefix).resolve()
        if not full_prefix.exists() or not full_prefix.is_dir():
            return []
        out: list[str] = []
        for p in full_prefix.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(self._root).as_posix()
            if rel.startswith(f"{VERSIONS_DIRNAME}/"):
                continue
            out.append(rel)
        out.sort()
        return out

    def list_versions(self, path: str) -> list[ObjectVersion]:
        versions: list[ObjectVersion] = []
        full = self._resolve(path)
        if full.exists():
            stat = full.stat()
            versions.append(
                ObjectVersion(
                    path=normalize_path(path),
                    version_id=str(stat.st_mtime_ns),
                    size=stat.st_size,
                    updated_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                    is_current=True,
                )
            )
        versions_dir = self._versions_dir(path)
        if versions_dir.exists():
            for v in sorted(versions_dir.iterdir(), reverse=True):
                if not v.is_file():
                    continue
                stat = v.stat()
                versions.append(
                    ObjectVersion(
                        path=normalize_path(path),
                        version_id=v.name,
                        size=stat.st_size,
                        updated_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                        is_current=False,
                    )
                )
        return versions

    def copy_prefix(self, src_prefix: str, dst_prefix: str) -> list[str]:
        src_paths = self.list_prefix(src_prefix)
        if not src_paths:
            return []
        src_prefix_n = normalize_path(src_prefix)
        dst_prefix_n = normalize_path(dst_prefix)
        written: list[str] = []
        for src in src_paths:
            rel = src[len(src_prefix_n) :].lstrip("/")
            dst = f"{dst_prefix_n}/{rel}"
            full_src = self._resolve(src)
            full_dst = self._resolve(dst)
            full_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(full_src, full_dst)
            written.append(dst)
        return written
