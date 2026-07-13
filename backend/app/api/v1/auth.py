"""Authentication endpoints: login, logout, refresh, current user."""

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_auth_service, get_current_user
from app.schemas.auth import LoginRequest, RefreshRequest
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, auth: AuthService = Depends(get_auth_service)) -> dict:
    user, tokens = auth.login(str(payload.email), payload.password, remember=payload.remember)
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
