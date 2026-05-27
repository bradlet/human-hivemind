"""Image proxy endpoint for domain card backgrounds.

Reads bytes from the storage backend (LocalStorage in dev, GCSStorage in prod)
and returns them as an HTTP response with the appropriate Content-Type. Returns
404 if no image exists at any supported extension — frontend falls back to a
CSS gradient in that case.
"""
from __future__ import annotations

import mimetypes
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from hivemind.api.deps import get_storage
from hivemind.storage import StorageBackend
from hivemind.storage.base import StoredObjectNotFound

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/domains/{slug}")
def get_domain_image(
    slug: str,
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> Response:
    for ext in ("jpg", "jpeg", "png", "webp", "svg"):
        try:
            obj = storage.read(f"images/domains/{slug}.{ext}")
        except StoredObjectNotFound:
            continue
        mime, _ = mimetypes.guess_type(f"x.{ext}")
        return Response(
            content=obj.data,
            media_type=mime or "application/octet-stream",
            headers={"Cache-Control": "public, max-age=3600"},
        )
    raise HTTPException(status_code=404, detail="Domain image not found")
