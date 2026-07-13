# Authentication & RBAC (Sprint 04)

WES OS is a protected application: only authenticated users may access it, and
every API validates the caller's permissions. Authentication is JWT-based;
authorization is role-based (RBAC). No new user store was introduced —
authentication is layered onto the existing **Employee** module.

## Authentication flow

```
Login (email + password)
  └─ bcrypt verify → issue Access JWT (30 min) + Refresh JWT (7d, 30d if "remember")
Access token → sent as `Authorization: Bearer <token>` on every API call
  └─ 401 → client silently calls /auth/refresh once → retries
Refresh token → /auth/refresh → new access token
Logout → increments refresh_token_version → all refresh tokens invalidated
```

- **Access token** — short-lived; claims: `sub` (employee id), `role`, `email`, `type=access`.
- **Refresh token** — long-lived; claims: `sub`, `ver` (matched to `refresh_token_version`), `type=refresh`.
- **Logout invalidation** — bumping `refresh_token_version` revokes every outstanding refresh token.
- **Passwords** — bcrypt hashes; never stored or returned in plaintext.
- **Lockout** — accounts lock after 5 consecutive failed logins (`failed_login_attempts`).

## Roles & permissions

| Role | Company write | Department write | Employee write | Reads (all) |
|------|:---:|:---:|:---:|:---:|
| **Founder** | ✅ | ✅ | ✅ | ✅ |
| **Director** | — | ✅ | ✅ | ✅ |
| **Department Head** | — | — | ✅ | ✅ |
| **Employee** | — | — | — | ✅ |
| **Read Only** | — | — | — | ✅ |

Reads = company / department / employee / dashboard. Enforced by a reusable
`require_permission(Permission.X)` dependency on every endpoint:
missing/invalid token → **401**, insufficient role → **403**.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Authenticate; returns user + access/refresh tokens |
| POST | `/api/v1/auth/refresh` | Exchange a refresh token for a new access token |
| POST | `/api/v1/auth/logout` | Revoke refresh tokens (requires auth) |
| GET | `/api/v1/auth/me` | Current authenticated user |

All existing Company Engine and Dashboard endpoints now require authentication
and the appropriate permission.

## Database changes

Migration `0002_auth_fields` adds to `employees` (Company Engine schema otherwise
unchanged): `role`, `password_hash`, `is_active`, `last_login`,
`failed_login_attempts`, `refresh_token_version`.

## Seeded development credentials

The seed assigns one of each role and a shared dev password
(`WES_SEED_DEFAULT_PASSWORD`, default `WesOs2026!`):

| Email | Role |
|-------|------|
| `wes-emp-001@wes.studio` | Founder |
| `wes-emp-002@wes.studio` | Director |
| `wes-emp-004@wes.studio` | Department Head |
| `wes-emp-006@wes.studio` | Employee |
| `wes-emp-013@wes.studio` | Read Only |

> These are development-only credentials. Set `WES_JWT_SECRET` and real passwords
> before any deployment.

## Frontend

- **SessionProvider** — holds the session, hydrates from stored tokens via `/auth/me`.
- **Login screen** — email/password/remember; `remember` persists tokens in
  localStorage, otherwise sessionStorage.
- **ProtectedRoute** — redirects unauthenticated users to `/login`.
- **API client** — attaches the bearer token, refreshes once on 401, routes 403 → `/forbidden`.
- **Pages** — Login, Forbidden (403), Unauthorized (401); sign-out in the sidebar.
