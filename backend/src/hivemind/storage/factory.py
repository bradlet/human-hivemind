"""Storage backend factory.

Reads `STORAGE_BACKEND` from settings and returns the appropriate concrete
backend. No GCS emulator in dev: local mode uses `LocalStorage` against the
filesystem root configured by `HIVEMIND_LOCAL_CONTENT_ROOT`.
"""
from __future__ import annotations

from hivemind.config import Settings
from hivemind.config import StorageBackend as Backend
from hivemind.storage.base import StorageBackend
from hivemind.storage.local import LocalStorage


def build_storage(settings: Settings) -> StorageBackend:
    if settings.storage_backend == Backend.LOCAL:
        return LocalStorage(settings.local_content_root)
    if settings.storage_backend == Backend.GCS:
        from hivemind.storage.gcs import GCSStorage
        return GCSStorage(bucket_name=settings.gcs_bucket, prefix=settings.gcs_prefix)
    raise ValueError(f"Unknown storage backend: {settings.storage_backend}")
