"""Typed application errors + FastAPI exception handlers.

Every response follows one envelope so the frontend can render friendly,
production-safe messages (no stack traces, DB errors, secrets or paths):

    { "error": { "code": "incorrect_flag", "message": "...", "details": {...} } }
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings


class AppError(Exception):
    """Base class for all expected, user-presentable failures."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "error"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message or self.default_message()
        self.code = code or self.code
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}
        self.headers = headers or {}
        super().__init__(self.message)

    @classmethod
    def default_message(cls) -> str:
        return "Something went wrong. Please try again."

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status_code,
            content={"error": {"code": self.code, "message": self.message, "details": self.details}},
            headers=self.headers,
        )


class BadRequest(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "bad_request"

    @classmethod
    def default_message(cls) -> str:
        return "The request could not be processed."


class ValidationFailed(AppError):
    status_code = 422  # HTTP_422_UNPROCESSABLE_CONTENT (avoid deprecated alias)
    code = "validation_error"

    @classmethod
    def default_message(cls) -> str:
        return "Some of the submitted values are invalid."


class Unauthorized(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"

    @classmethod
    def default_message(cls) -> str:
        return "You must sign in to continue."

    def __init__(self, message: str | None = None, **kwargs: Any) -> None:
        headers = kwargs.pop("headers", None) or {"WWW-Authenticate": "Bearer"}
        super().__init__(message, headers=headers, **kwargs)


class Forbidden(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"

    @classmethod
    def default_message(cls) -> str:
        return "You do not have permission to perform this action."


class NotFound(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"

    @classmethod
    def default_message(cls) -> str:
        return "The requested resource was not found."


class Conflict(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"

    @classmethod
    def default_message(cls) -> str:
        return "That action conflicts with the current state."


class RateLimited(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limited"

    @classmethod
    def default_message(cls) -> str:
        return "Too many requests. Please slow down and try again shortly."

    def __init__(self, message: str | None = None, *, retry_after: int = 60, **kwargs: Any) -> None:
        details = kwargs.pop("details", {})
        super().__init__(
            message,
            headers={"Retry-After": str(max(1, retry_after))},
            details={"retry_after": max(1, retry_after), **details},
            **kwargs,
        )


class AccountDisabled(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "account_disabled"

    @classmethod
    def default_message(cls) -> str:
        return "This account has been disabled by the organisers. Contact WANO CTF support."


class TeamRequired(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "team_required"

    @classmethod
    def default_message(cls) -> str:
        return "You must create or join a team before solving challenges."


class TeamLocked(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "team_locked"

    @classmethod
    def default_message(cls) -> str:
        return "Team membership is locked. Teams can no longer be changed."


class CompetitionNotStarted(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "competition_not_started"

    @classmethod
    def default_message(cls) -> str:
        return "The competition has not started yet. Stand by, hacker."


class CompetitionEnded(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "competition_ended"

    @classmethod
    def default_message(cls) -> str:
        return "CTF HAS ENDED. Submissions are now closed."


class CompetitionPaused(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "competition_paused"

    @classmethod
    def default_message(cls) -> str:
        return "The competition is temporarily paused. Submissions are on hold."


class AlreadySolved(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "already_solved"

    @classmethod
    def default_message(cls) -> str:
        return "Challenge already solved."


class IncorrectFlag(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "incorrect_flag"

    @classmethod
    def default_message(cls) -> str:
        return "Incorrect flag."


class AttemptsExhausted(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "attempts_exhausted"

    @classmethod
    def default_message(cls) -> str:
        return "You have used all attempts for this challenge."


class StorageError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "storage_error"

    @classmethod
    def default_message(cls) -> str:
        return "The file could not be stored securely. Check the type and size."


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return exc.to_response()

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = {
            "fields": [
                {"loc": ".".join(str(p) for p in err.get("loc", [])), "msg": err.get("msg", "invalid")}
                for err in exc.errors()[:20]
            ]
        }
        return ValidationFailed(details=details).to_response()

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        mapping = {
            401: ("unauthorized", "You must sign in to continue."),
            403: ("forbidden", "You do not have permission to perform this action."),
            404: ("not_found", "The requested resource was not found."),
            405: ("method_not_allowed", "That method is not allowed on this endpoint."),
            429: ("rate_limited", "Too many requests. Please slow down."),
        }
        code, message = mapping.get(
            exc.status_code, ("error", str(exc.detail) if exc.detail else "Request failed.")
        )
        return JSONResponse(
            status_code=exc.status_code, content={"error": {"code": code, "message": message}}
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # Never leak internals: log server-side, return a generic envelope.
        import logging

        logging.getLogger("wano.errors").exception("Unhandled error: %s", exc)
        message = (
            f"{type(exc).__name__}: {exc}"
            if settings.debug
            else "An unexpected server error occurred. Please try again."
        )
        return JSONResponse(
            status_code=500, content={"error": {"code": "internal_error", "message": message}}
        )

