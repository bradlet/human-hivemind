"""Abstract storage backend.

The pipeline interacts with content storage through this interface only. Two
concrete implementations: `LocalStorage` (filesystem-backed, used in dev) and
`GCSStorage` (Google Cloud Storage with object versioning, used in prod).

Paths are POSIX-style strings (forward-slash separated) regardless of backend.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


class StoredObjectNotFound(Exception):
    """Raised when a path doesn't exist in the backend."""


@dataclass(frozen=True)
class ObjectVersion:
    """A historical version of an object."""

    path: str
    version_id: str
    size: int
    updated_at: datetime
    is_current: bool


@dataclass(frozen=True)
class StoredObject:
    """The current state of an object."""

    path: str
    data: bytes
    version_id: str | None
    updated_at: datetime | None


class StorageBackend(ABC):
    """Content storage interface. All methods operate on POSIX path strings."""

    @abstractmethod
    def read(self, path: str, *, version_id: str | None = None) -> StoredObject:
        """Read an object, optionally a prior version. Raises StoredObjectNotFound."""

    @abstractmethod
    def write(self, path: str, data: bytes) -> StoredObject:
        """Write (or overwrite) an object. Returns the new state."""

    @abstractmethod
    def delete(self, path: str) -> None:
        """Delete an object. No-op if it doesn't exist."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Return True if an object exists at `path`."""

    @abstractmethod
    def list_prefix(self, prefix: str) -> list[str]:
        """List all object paths under a prefix. Returns sorted POSIX paths."""

    @abstractmethod
    def list_versions(self, path: str) -> list[ObjectVersion]:
        """List historical versions of a path (newest first). Empty list if none."""

    @abstractmethod
    def copy_prefix(self, src_prefix: str, dst_prefix: str) -> list[str]:
        """Recursively copy all objects under src_prefix to dst_prefix.

        Returns the list of destination paths written.
        """


def normalize_path(path: str) -> str:
    """Normalize a storage path: forward slashes, no leading slash, no trailing slash."""
    p = path.replace("\\", "/").strip("/")
    if not p:
        raise ValueError("Storage path cannot be empty")
    if ".." in p.split("/"):
        raise ValueError(f"Storage path may not contain '..': {path!r}")
    return p
