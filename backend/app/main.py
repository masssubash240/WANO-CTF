"""Root application factory, exception handlers and lifespan wiring."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app import __version__
from app.api.router import api_router
from app.config import settings
from app.errors import AppError
from app.logging_config import configure_logging
from app.middleware import register_middleware

logger = logging.getLogger("wano")


def _cors_origins() -> list[str]:
    return settings.cors_origin_list


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting WANO CTF API %s (env=%s)", __version__, settings.environment)
    if settings.is_production and not settings.supabase_configured:
        logger.warning("SUPABASE_URL/keys are not configured; participant auth will fail.")
    yield
    logger.info("WANO CTF API shut down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="WANO CTF platform API — challenges, teams, scoring and operations.",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Retry-After"],
        max_age=600,
    )
    register_middleware(app)

    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        """Single error contract for the whole API (see ``app.errors``)."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Field errors can echo the submitted value — for a flag endpoint that
        # would defeat the point, so only the location and type are surfaced.
        fields = [
            {"field": ".".join(str(p) for p in err.get("loc", ())[1:]), "reason": err.get("msg", "")}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Some of the submitted values are not valid.",
                    "details": {"fields": fields},
                }
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def _db_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("Unhandled database error on %s", request.url.path)
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "service_unavailable",
                    "message": "The service is temporarily unavailable. Please try again.",
                    "details": {},
                }
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("Unhandled error on %s (request_id=%s)", request.url.path, request_id)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Something went wrong on our side.",
                    "details": {"request_id": request_id} if request_id else {},
                }
            },
        )

    @app.get("/health", tags=["system"], include_in_schema=False)
    async def health() -> dict[str, object]:
        return {
            "status": "ok",
            "version": __version__,
            "environment": settings.environment,
        }

    app.include_router(api_router)
    return app


app = create_app()
