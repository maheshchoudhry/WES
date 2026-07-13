"""WES Web Application — backend entrypoint.

Sprint 01 provides the application factory and a health endpoint only.
Feature routers are registered under /api/v1 in later sprints.
"""
from fastapi import FastAPI

from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.api_version,
    )

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    # Feature routers (registered in later sprints):
    # from app.api.v1.router import api_router
    # app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
