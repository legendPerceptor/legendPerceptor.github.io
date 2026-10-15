"""Input normalisation helpers (stdlib only, so they are trivial to unit test)."""

from __future__ import annotations

import hashlib
import re

MAX_EMAIL_LENGTH = 254
MAX_LOCAL_LENGTH = 64

_LOCAL_PART = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+"
_DOMAIN_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
_EMAIL_RE = re.compile(rf"^{_LOCAL_PART}@{_DOMAIN_LABEL}(?:\.{_DOMAIN_LABEL})+$")


def normalize_email(raw: object) -> str | None:
    """Return the canonical form of ``raw`` or ``None`` when it is not an address.

    The whole address is lower-cased: it keeps the UNIQUE index meaningful and
    matches how every mail provider treats addresses in practice.
    """

    if not isinstance(raw, str):
        return None

    email = raw.strip().strip("<>").strip()
    if not email or len(email) > MAX_EMAIL_LENGTH:
        return None
    if "@" not in email:
        return None

    local, _, domain = email.rpartition("@")
    if not local or not domain or len(local) > MAX_LOCAL_LENGTH:
        return None
    if local.startswith(".") or local.endswith(".") or ".." in local:
        return None
    if ".." in domain or domain.startswith("-") or domain.endswith("-"):
        return None

    email = f"{local}@{domain}"
    if not _EMAIL_RE.match(email):
        return None
    return email.lower()


def clean_text(raw: object, *, max_length: int = 200) -> str | None:
    """Trim a free-text field (``source``, ``user_agent``) down to a sane size."""

    if raw is None:
        return None
    if not isinstance(raw, str):
        raw = str(raw)
    value = " ".join(raw.split())
    if not value:
        return None
    return value[:max_length]


def hash_ip(ip: str | None, salt: str) -> str | None:
    """Store a salted hash instead of the raw address (privacy by default)."""

    if not ip:
        return None
    digest = hashlib.sha256(f"{salt}:{ip}".encode("utf-8")).hexdigest()
    return digest[:32]
