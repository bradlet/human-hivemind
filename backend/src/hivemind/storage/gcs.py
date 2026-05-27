"""Google Cloud Storage backend.

Relies on the bucket having Object Versioning enabled (configure via:
`gsutil versioning set on gs://your-bucket`). Reads with no `version_id` fetch
the current object; reads with a `version_id` fetch a specific generation.

Authentication uses Application Default Credentials; the prod container should
run with a service account that has Storage Object Admin on the bucket.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from hivemind.storage.base import (
    ObjectVersion,
    StorageBackend,
    StoredObject,
    StoredObjectNotFound,
    normalize_path,
)

if TYPE_CHECKING:
    from google.cloud.storage import Blob, Bucket, Client


class GCSStorage(StorageBackend):
    def __init__(self, bucket_name: str, prefix: str = "") -> None:
        if not bucket_name:
            raise ValueError("GCSStorage requires a non-empty bucket name")
        from google.cloud import storage

        self._client: Client = storage.Client()
        self._bucket: Bucket = self._client.bucket(bucket_name)
        self._prefix = prefix.strip("/")

    def _key(self, path: str) -> str:
        p = normalize_path(path)
        if self._prefix:
            return f"{self._prefix}/{p}"
        return p

    def _strip_prefix(self, key: str) -> str:
        if self._prefix and key.startswith(f"{self._prefix}/"):
            return key[len(self._prefix) + 1 :]
        return key

    def read(self, path: str, *, version_id: str | None = None) -> StoredObject:
        from google.api_core.exceptions import NotFound

        key = self._key(path)
        generation = int(version_id) if version_id else None
        blob: Blob = self._bucket.blob(key, generation=generation)
        try:
            data = blob.download_as_bytes()
        except NotFound as exc:
            raise StoredObjectNotFound(path) from exc
        blob.reload()
        updated = blob.updated.replace(tzinfo=UTC) if blob.updated else None
        return StoredObject(
            path=normalize_path(path),
            data=data,
            version_id=str(blob.generation) if blob.generation else None,
            updated_at=updated,
        )

    def write(self, path: str, data: bytes) -> StoredObject:
        key = self._key(path)
        blob: Blob = self._bucket.blob(key)
        blob.upload_from_string(data)
        blob.reload()
        updated = blob.updated.replace(tzinfo=UTC) if blob.updated else None
        return StoredObject(
            path=normalize_path(path),
            data=data,
            version_id=str(blob.generation) if blob.generation else None,
            updated_at=updated,
        )

    def delete(self, path: str) -> None:
        from google.api_core.exceptions import NotFound

        key = self._key(path)
        try:
            self._bucket.blob(key).delete()
        except NotFound:
            return

    def exists(self, path: str) -> bool:
        return self._bucket.blob(self._key(path)).exists()

    def list_prefix(self, prefix: str) -> list[str]:
        full_prefix = self._key(prefix) + "/"
        blobs = self._client.list_blobs(self._bucket, prefix=full_prefix)
        out = [self._strip_prefix(b.name) for b in blobs if not b.name.endswith("/")]
        out.sort()
        return out

    def list_versions(self, path: str) -> list[ObjectVersion]:
        key = self._key(path)
        blobs = list(self._client.list_blobs(self._bucket, prefix=key, versions=True))
        blobs = [b for b in blobs if b.name == key]
        blobs.sort(key=lambda b: b.generation or 0, reverse=True)
        result: list[ObjectVersion] = []
        for b in blobs:
            updated = b.updated.replace(tzinfo=UTC) if b.updated else datetime.now(UTC)
            result.append(
                ObjectVersion(
                    path=normalize_path(path),
                    version_id=str(b.generation),
                    size=b.size or 0,
                    updated_at=updated,
                    is_current=b.time_deleted is None,
                )
            )
        return result

    def copy_prefix(self, src_prefix: str, dst_prefix: str) -> list[str]:
        src_key = self._key(src_prefix)
        dst_key = self._key(dst_prefix)
        src_key_pref = src_key if src_key.endswith("/") else src_key + "/"
        blobs = list(self._client.list_blobs(self._bucket, prefix=src_key_pref))
        written: list[str] = []
        for blob in blobs:
            rel = blob.name[len(src_key_pref) :]
            new_name = f"{dst_key}/{rel}" if rel else dst_key
            self._bucket.copy_blob(blob, self._bucket, new_name=new_name)
            written.append(self._strip_prefix(new_name))
        return written
