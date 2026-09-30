"""Flag handling — the single most sensitive code path in WANO CTF.

Guarantees:
  1. The plaintext flag is stored **nowhere** (only a peppered HMAC digest).
  2. Verification is server-side only and uses constant-time comparison.
  3. Nothing in the public/serialised API surface can leak a digest or a flag.
  4. Submitted values are hashed + masked before they reach the database.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import unicodedata

from app.config import settings

#: Characters tolerated at the edges of a submission (copy/paste noise).
_EDGE_JUNK = "\"'`,;<>[]() \t\r\n\u200b\u200c\u200d\ufeff"

_ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\ufeff]")
_OUTER_WRAPPER = re.compile(r"^[`\"']+|[`\"']+$")
_WHITESPACE_RUN = re.compile(r"\s+")

MAX_FLAG_LENGTH = 512


def normalize_flag(flag: str) -> str:
    """Canonicalise a flag so trivial paste noise does not cause false negatives.

    Case is preserved (CTF flags are case-sensitive); we only strip zero-width
    characters, collapsing runs of whitespace to a single space and trimming
    enclosing quotes/backticks.
    """
    if not isinstance(flag, str):
        return ""
    value = unicodedata.normalize("NFKC", flag)
    value = _ZERO_WIDTH.sub("", value)
    value = value.strip(_EDGE_JUNK)
    value = _OUTER_WRAPPER.sub("", value)
    value = _WHITESPACE_RUN.sub(" ", value).strip()
    return value[:MAX_FLAG_LENGTH]


def hash_flag(flag: str, pepper: str | None = None) -> str:
    """HMAC-SHA256 of the normalised flag. This is all we ever persist."""
    normalized = normalize_flag(flag)
    key = (pepper or settings.flag_pepper).encode("utf-8")
    return hmac.new(key, normalized.encode("utf-8"), hashlib.sha256).hexdigest()


def flag_matches(submitted_flag: str, stored_hash: str | None) -> bool:
    """Constant-time comparison against the stored digest."""
    if not submitted_flag or not stored_hash:
        return False
    candidate = hash_flag(submitted_flag)
    return hmac.compare_digest(candidate, stored_hash)


def looks_like_flag(candidate: str, pattern: str | None = None) -> bool:
    """Loose sanity check so obvious junk never hits the verification path."""
    value = normalize_flag(candidate)
    if not value or len(value) < 4:
        return False
    if pattern:
        return bool(re.fullmatch(pattern, value))
    return True


def mask_flag(candidate: str, keep: int = 5) -> str:
    """Safe-for-storage representation, e.g. ``WANO{****#28}``.

    Retains at most ``keep`` leading characters plus the length so organisers can
    spot brute-force patterns during an investigation without storing a usable
    flag dump.
    """
    value = normalize_flag(candidate)
    if not value:
        return ""
    prefix = value[:keep]
    return f"{prefix}{'*' * min(8, max(0, len(value) - len(prefix)))}#{len(value)}"


def submission_fingerprint(candidate: str) -> str:
    """Salted digest of the *raw* submission (dedupe / brute-force detection)."""
    value = normalize_flag(candidate)
    return hashlib.sha256(f"wano-submission::{value}".encode()).hexdigest()


def constant_time_equals(left: str | None, right: str | None) -> bool:
    if left is None or right is None:
        return False
    return hmac.compare_digest(left, right)
