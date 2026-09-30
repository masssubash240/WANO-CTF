"""ASGI middleware: request correlation, security headers and a coarse IP limiter."""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config import settings
from app.security.deps import client_ip
from app.security.rate_limit import limiter

#: Paths that never consume the anonymous IP budget.
_EXEMPT_PREFIXES = ("/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico")

_ANON_LIMIT_PER_MINUTE = 240


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attaches a request id + latency and echoes it back to the client."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-ms"] = f"{elapsed_ms:.1f}"
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """OWASP-recommended response headers (browser-side hardening)."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        if not settings.security_headers_enabled:
            return response

        headers = response.headers
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=(), payment=(), usb=(), clipboard-write=(self)",
        )
        headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
        headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
        )
        if settings.is_production:
            headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload"
            )
        return response


class AnonymousIpRateLimitMiddleware(BaseHTTPMiddleware):
    """Blunt-trauma protection for unauthenticated traffic and API enumeration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if (
            not settings.rate_limit_enabled
            or request.method == "OPTIONS"
            or any(path.startswith(prefix) for prefix in _EXEMPT_PREFIXES)
        ):
            return await call_next(request)

        result = await limiter.hit(
            f"ip:{client_ip(request)}", limit=_ANON_LIMIT_PER_MINUTE, window_seconds=60
        )
        if not result.allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "rate_limited",
                        "message": "Too many requests from this network. Please wait a moment.",
                        "details": {"retry_after": result.retry_after},
                    }
                },
                headers={"Retry-After": str(result.retry_after)},
            )
        return await call_next(request)


def register_middleware(app: FastAPI) -> None:
    # Outermost first: security headers should wrap every response, including
    # limiter rejections, and every response gets a request id.
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(AnonymousIpRateLimitMiddleware)
    app.add_middleware(RequestContextMiddleware)
