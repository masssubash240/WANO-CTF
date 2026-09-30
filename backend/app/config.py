"""Application settings.

All configuration is environment driven so the API can be deployed to
Render / Railway / a VPS without code changes. Secrets are *never* returned to
clients: see ``app/api/v1/routes/auth.py`` ``/auth/config`` which only exposes
the provider mode + public Supabase URL/anon key.
"""

from __future__ import annotations

import functools
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------------- App ----------------
    app_name: str = "WANO CTF API"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = True
    api_prefix: str = "/api"
    frontend_url: str = "http://localhost:5173"
    site_url: str = "https://ctf.wano-fest.com"

    # ---------------- Supabase ----------------
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_jwks_url: str = ""
    supabase_storage_bucket: str = "challenge-files"

    # ---------------- Database ----------------
    database_url: str = "sqlite+aiosqlite:///./wano_ctf_dev.db"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    # ---------------- Auth ----------------
    jwt_secret: str = "dev-insecure-jwt-secret-change-me"
    admin_jwt_secret: str = "dev-insecure-admin-jwt-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60
    flag_pepper: str = "dev-insecure-flag-pepper-change-me"
    admin_email: str = "admin@wano-fest.com"
    admin_password: str = "ChangeMe_Strong#2026"
    dev_auth_enabled: bool = False
    allow_admin_supabase_login: bool = False
    email_verification_required: bool = False
    google_oauth_enabled: bool = False
    password_reset_enabled: bool = True
    trust_proxy_headers: bool = False

    # ---------------- Rate limits (per minute) ----------------
    rate_limit_register_per_minute: int = 10
    rate_limit_login_per_minute: int = 20
    rate_limit_password_reset_per_minute: int = 5

    # ---------------- Competition ----------------
    ctf_timezone: str = "Asia/Kolkata"

    # ---------------- CORS / security ----------------
    cors_origins: str = "http://localhost:5173"
    allowed_hosts: str = "*"
    security_headers_enabled: bool = True
    rate_limit_enabled: bool = True
    rate_limit_redis_url: str = ""

    # ---------------- Uploads ----------------
    storage_backend: Literal["local", "supabase"] = "local"
    local_storage_dir: str = "./storage"
    max_upload_mb: int = 64
    allowed_upload_extensions: str = (
        ".zip,.tar,.gz,.tgz,.7z,.rar,.pdf,.txt,.md,.csv,.json,.xml,.pcap,.pcapng,.cap,"
        ".png,.jpg,.jpeg,.gif,.svg,.py,.js,.ts,.java,.c,.cpp,.h,.go,.rb,.php,.sh,.sql,"
        ".elf,.bin,.so,.dll,.exe,.apk"
    )

    # ---------------- Observability ----------------
    log_level: str = "INFO"
    audit_log_enabled: bool = True


    # ------------------------------------------------------------------ helpers
    @field_validator("api_prefix")
    @classmethod
    def _normalize_prefix(cls, value: str) -> str:
        if not value.startswith("/"):
            value = "/" + value
        return value.rstrip("/") or ""

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        raw = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if not raw:
            raw = ["http://localhost:5173"]
        return raw

    @property
    def allowed_host_list(self) -> list[str]:
        raw = [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]
        return raw or ["*"]

    @property
    def allowed_extension_set(self) -> set[str]:
        return {e.strip().lower() for e in self.allowed_upload_extensions.split(",") if e.strip()}

    @property
    def jwks_url(self) -> str:
        if self.supabase_jwks_url:
            return self.supabase_jwks_url
        if not self.supabase_url:
            return ""
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key)

    @property
    def supabase_admin_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)

    @property
    def auth_provider(self) -> Literal["supabase", "local"]:
        """Supabase in real deployments; local provider only for dev/test."""
        if self.dev_auth_enabled:
            return "local"
        return "supabase"

    def assert_production_ready(self) -> list[str]:
        """Return a list of misconfiguration warnings (never fatal at import)."""
        problems: list[str] = []
        if not self.is_production:
            return problems
        if "change-me" in self.jwt_secret or "insecure" in self.jwt_secret:
            problems.append("JWT_SECRET must be set to a strong random value in production.")
        if "change-me" in self.admin_jwt_secret or "insecure" in self.admin_jwt_secret:
            problems.append("ADMIN_JWT_SECRET must be set to a strong random value in production.")
        if "change-me" in self.flag_pepper or "insecure" in self.flag_pepper:
            problems.append("FLAG_PEPPER must be set to a strong random value in production.")
        if self.dev_auth_enabled:
            problems.append("DEV_AUTH_ENABLED must be false in production.")
        if self.database_url.startswith("sqlite"):
            problems.append("DATABASE_URL must point at Supabase PostgreSQL in production.")
        if "*" in self.cors_origin_list:
            problems.append("CORS_ORIGINS must not contain '*' in production.")
        return problems


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
