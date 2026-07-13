"""FastAPI application factory for the WES Company Engine.

Wires the API router, CORS, and the exception handlers that translate domain
errors and request-validation failures into the standard error envelope.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import DomainError

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup so the schema (and seed) are present.

    Controlled by ``WES_AUTO_MIGRATE`` / ``WES_SEED_ON_START``. This makes the
    backend self-initializing — a freshly cloned project runs without a separate
    manual migration step.
    """
    settings = get_settings()
    if settings.auto_migrate:
        from app.db.init import init_database

        init_database(seed_data=settings.seed_on_start)
    else:
        logger.info("Auto-migration disabled (WES_AUTO_MIGRATE=false).")
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="WES OS — Core Company Engine (Company, Departments, Employees).",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(DomainError)
    async def _domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {"code": exc.code, "message": exc.message, "details": exc.details}
            },
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": ".".join(str(p) for p in err["loc"]), "message": err["msg"]}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": details,
                }
            },
        )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/")
    def root() -> dict:
        return {"data": {"service": settings.app_name, "version": __version__}}

    return app


app = create_app()
