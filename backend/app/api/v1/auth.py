"""Authentication endpoints: login, logout, refresh, current user."""

from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, get_auth_service, get_current_user
from app.schemas.auth import LoginRequest, RefreshRequest
from app.services.auth import AuthError, AuthService
from app.services.audit import AuditService

router = APIRouter(prefix="/auth", tags=["auth"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/login")
def login(
    payload: LoginRequest, request: Request, auth: AuthService = Depends(get_auth_service)
) -> dict:
    audit = AuditService(auth.db)
    try:
        user, tokens = auth.login(str(payload.email), payload.password, remember=payload.remember)
    except AuthError:
        # WP5 security event: failed login. Committed on the request session so it
        # survives the rollback that accompanies the 401.
        audit.security_event("login_failed", actor=str(payload.email), ip=_ip(request))
        auth.db.commit()
        raise
    audit.record("login", actor=user.email, category="auth", ip=_ip(request), entity_type="employee", entity_id=str(user.id))
    return {"data": {"user": user, "tokens": tokens}}


@router.post("/refresh")
def refresh(payload: RefreshRequest, auth: AuthService = Depends(get_auth_service)) -> dict:
    tokens = auth.refresh(payload.refresh_token)
    return {"data": {"tokens": tokens}}


@router.post("/logout")
def logout(
    user: CurrentUser = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
) -> dict:
    auth.logout(user.id)
    return {"data": {"status": "logged_out"}}


@router.get("/me")
def me(
    user: CurrentUser = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
) -> dict:
    return {"data": auth.authenticated_user(user.id)}
