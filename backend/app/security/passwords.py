"""Password hashing with stdlib scrypt (no native build dependencies).

Used for:
  * admin panel credentials (always, independent of Supabase Auth)
  * participant credentials in the local dev/test provider only

Format: ``scrypt$n$r$p$<salt_b64>$<hash_b64>``
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16
KEY_LEN = 32
ALGORITHM = "scrypt"


def _b64e(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _b64d(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


def hash_password(password: str) -> str:
    if not isinstance(password, str) or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if len(password) > 256:
        raise ValueError("Password is too long.")
    salt = secrets.token_bytes(SALT_BYTES)
    derived = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=KEY_LEN
    )
    return f"{ALGORITHM}${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${_b64e(salt)}${_b64e(derived)}"


def verify_password(password: str, stored: str | None) -> bool:
    """Constant-time verification. Returns False for malformed hashes."""
    if not stored or not password:
        return False
    try:
        algorithm, n, r, p, salt_b64, hash_b64 = stored.split("$")
        if algorithm != ALGORITHM:
            return False
        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=_b64d(salt_b64),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(_b64d(hash_b64)),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(derived, _b64d(hash_b64))


def password_strength_errors(password: str) -> list[str]:
    """Cheap policy check used by validators (never logs the password)."""
    problems: list[str] = []
    if len(password) < 8:
        problems.append("Password must be at least 8 characters long.")
    if len(password) > 256:
        problems.append("Password must be at most 256 characters long.")
    if password.isalpha() or password.isdigit():
        problems.append("Password must mix letters with numbers or symbols.")
    return problems
