# Alembic Migrations

Database schema migrations for the WES Company Engine.

- The database URL comes from `WES_DATABASE_URL` (see `../.env.example`); it is
  **not** stored in `alembic.ini`.
- Target metadata is `app.models.Base.metadata`, so migrations track the ORM models.

## Common commands

Run from the `backend/` directory with the virtualenv active:

```bash
alembic upgrade head          # apply all migrations
alembic downgrade -1          # roll back one migration
alembic revision --autogenerate -m "message"   # scaffold a new migration
alembic current               # show current revision
alembic history               # list migration history
```
