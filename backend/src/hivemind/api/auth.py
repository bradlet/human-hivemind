"""Google OAuth via Authlib. httpOnly session cookies carry the user id.

In dev, when OAuth isn't configured (no client id/secret), a `dev-login`
endpoint exists for convenience that takes an email and signs the user in
without a real OAuth exchange. The frontend hides this route in production.
"""
from __future__ import annotations

import secrets
from typing import Annotated

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from hivemind.api.deps import current_user_required, get_db, get_settings_dep
from hivemind.api.schemas import AuthMeOut
from hivemind.config import Settings
from hivemind.db.models import UserRow
from hivemind.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

_oauth_singleton: OAuth | None = None


def _oauth(settings: Settings) -> OAuth:
    global _oauth_singleton
    if _oauth_singleton is not None:
        return _oauth_singleton
    oauth = OAuth()
    if settings.oauth_enabled:
        oauth.register(
            name="google",
            client_id=settings.google_oauth_client_id,
            client_secret=settings.google_oauth_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    _oauth_singleton = oauth
    return oauth


def _user_id_for_google_sub(google_sub: str) -> str:
    return f"google:{google_sub}"


def _upsert_user(
    db: Session, *, google_sub: str, email: str, name: str, avatar_url: str | None
) -> UserRow:
    user_id = _user_id_for_google_sub(google_sub)
    row = db.get(UserRow, user_id)
    if row is None:
        row = UserRow(
            id=user_id,
            google_sub=google_sub,
            email=email,
            name=name,
            avatar_url=avatar_url,
        )
        db.add(row)
    else:
        row.email = email
        row.name = name
        row.avatar_url = avatar_url
    db.flush()
    return row


@router.get("/google")
async def google_login(
    request: Request, settings: Annotated[Settings, Depends(get_settings_dep)]
) -> RedirectResponse:
    if not settings.oauth_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured on this server.",
        )
    oauth = _oauth(settings)
    return await oauth.google.authorize_redirect(request, settings.google_oauth_redirect_url)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings_dep)],
    db: Annotated[Session, Depends(get_db)],
) -> RedirectResponse:
    if not settings.oauth_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured on this server.",
        )
    oauth = _oauth(settings)
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as exc:
        raise HTTPException(status_code=400, detail=f"OAuth error: {exc.error}") from exc
    userinfo = token.get("userinfo") or {}
    sub = userinfo.get("sub")
    if not sub:
        raise HTTPException(status_code=400, detail="Google userinfo did not include 'sub'")
    row = _upsert_user(
        db,
        google_sub=sub,
        email=userinfo.get("email") or "",
        name=userinfo.get("name") or userinfo.get("email") or sub,
        avatar_url=userinfo.get("picture"),
    )
    request.session["user_id"] = row.id
    return RedirectResponse(url="/", status_code=302)


class DevLoginIn(BaseModel):
    email: str
    name: str | None = None


@router.post("/dev-login", response_model=AuthMeOut)
def dev_login(
    body: DevLoginIn,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings_dep)],
    db: Annotated[Session, Depends(get_db)],
) -> AuthMeOut:
    """Local-dev-only shortcut: sign in as the given email without OAuth.

    Disabled in production environments. Useful for E2E tests too.
    """
    if not settings.is_local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="dev-login is disabled"
        )
    sub = f"dev-{secrets.token_hex(4)}-{body.email.lower()}"
    row = _upsert_user(
        db,
        google_sub=sub,
        email=body.email,
        name=body.name or body.email.split("@")[0],
        avatar_url=None,
    )
    request.session["user_id"] = row.id
    return AuthMeOut(id=row.id, email=row.email, name=row.name, avatar_url=row.avatar_url)


@router.get("/me", response_model=AuthMeOut)
def me(user: Annotated[User, Depends(current_user_required)]) -> AuthMeOut:
    return AuthMeOut(id=user.id, email=user.email, name=user.name, avatar_url=user.avatar_url)


@router.post("/logout")
def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"ok": True}
