"""Unit tests for password hashing, JWT tokens, and the RBAC matrix."""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import get_settings
from app.domain.roles import Permission, Role, role_has_permission
from app.services.password import PasswordService
from app.services.tokens import TokenError, TokenService


# --- Password service ---------------------------------------------------


def test_password_hash_and_verify():
    svc = PasswordService()
    h = svc.hash("WesOs2026!")
    assert h != "WesOs2026!"
    assert svc.verify("WesOs2026!", h) is True
    assert svc.verify("wrong", h) is False


def test_verify_rejects_missing_hash():
    assert PasswordService().verify("x", None) is False


# --- Token service ------------------------------------------------------


def test_access_token_roundtrip():
    svc = TokenService()
    uid = uuid.uuid4()
    token = svc.create_access_token(subject=uid, role="founder", email="f@wes.studio")
    claims = svc.decode_access(token)
    assert claims.subject == uid
    assert claims.role == "founder"
    assert claims.email == "f@wes.studio"


def test_refresh_token_roundtrip():
    svc = TokenService()
    uid = uuid.uuid4()
    token = svc.create_refresh_token(subject=uid, version=3)
    claims = svc.decode_refresh(token)
    assert claims.subject == uid
    assert claims.version == 3


def test_access_token_rejected_as_refresh():
    svc = TokenService()
    token = svc.create_access_token(subject=uuid.uuid4(), role="founder", email="f@x.co")
    with pytest.raises(TokenError):
        svc.decode_refresh(token)


def test_expired_token_raises():
    settings = get_settings()
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": str(uuid.uuid4()), "type": "access", "role": "founder", "email": "e@x.co",
         "iat": now - timedelta(hours=2), "exp": now - timedelta(hours=1)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(TokenError):
        TokenService().decode_access(token)


def test_tampered_token_raises():
    with pytest.raises(TokenError):
        TokenService().decode_access("not.a.jwt")


# --- RBAC matrix --------------------------------------------------------


def test_founder_has_all_permissions():
    assert all(role_has_permission(Role.FOUNDER, p) for p in Permission)


def test_role_write_gradient():
    # Company write: founder only.
    assert role_has_permission(Role.FOUNDER, Permission.COMPANY_WRITE)
    assert not role_has_permission(Role.DIRECTOR, Permission.COMPANY_WRITE)
    # Department write: founder + director.
    assert role_has_permission(Role.DIRECTOR, Permission.DEPARTMENT_WRITE)
    assert not role_has_permission(Role.DEPARTMENT_HEAD, Permission.DEPARTMENT_WRITE)
    # Employee write: founder, director, department_head.
    assert role_has_permission(Role.DEPARTMENT_HEAD, Permission.EMPLOYEE_WRITE)
    assert not role_has_permission(Role.EMPLOYEE, Permission.EMPLOYEE_WRITE)
    assert not role_has_permission(Role.READ_ONLY, Permission.EMPLOYEE_WRITE)


def test_all_roles_can_read():
    for role in Role:
        assert role_has_permission(role, Permission.DASHBOARD_READ)
        assert role_has_permission(role, Permission.DEPARTMENT_READ)
