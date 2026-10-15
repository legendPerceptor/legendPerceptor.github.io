"""Runtime configuration for the subscription API.

Everything is read from environment variables so the same image can run on a
VPS, a NAS or in Docker without edits. See `.env.example`.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_ORIGINS = (
    "https://www.yuanjianliu.net",
    "https://legendperceptor.github.io",
    "http://localhost:4000",
    "http://127.0.0.1:4000",
)

DEFAULT_SITE_URL = "https://www.yuanjianliu.net"


def _as_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(raw: str | None, default: int) -> int:
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _as_list(raw: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if raw is None or raw.strip() == "":
        return default
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    """Resolved settings. Build with :func:`load_settings`."""

    db_path: Path
    allowed_origins: tuple[str, ...] = DEFAULT_ORIGINS
    admin_token: str = ""
    ip_salt: str = ""
    trust_proxy: bool = False
    site_url: str = DEFAULT_SITE_URL
    rate_limit: int = 5
    rate_window_seconds: int = 600
    max_body_bytes: int = 4096
    ip_salt_is_default: bool = False
    warnings: tuple[str, ...] = field(default=())

    @property
    def admin_enabled(self) -> bool:
        return bool(self.admin_token)


def load_settings(env: dict[str, str] | None = None) -> Settings:
    """Build :class:`Settings` from ``env`` (defaults to ``os.environ``)."""

    env = os.environ if env is None else env
    warnings: list[str] = []

    data_dir = Path(env.get("DATA_DIR") or "data").expanduser()
    db_path = data_dir / (env.get("DB_FILE") or "subscribers.db")

    admin_token = (env.get("ADMIN_TOKEN") or "").strip()
    if not admin_token:
        warnings.append(
            "ADMIN_TOKEN is empty: the /api/admin/* endpoints are disabled "
            "(set one to export or manage subscribers over HTTP)."
        )

    ip_salt = (env.get("IP_SALT") or "").strip()
    if not ip_salt:
        ip_salt = "insecure-default-salt"
        warnings.append(
            "IP_SALT is empty: a fixed default salt is used for IP hashing. "
            "Set IP_SALT to a random string."
        )

    rate_limit = _as_int(env.get("RATE_LIMIT"), 5)
    rate_window_seconds = _as_int(env.get("RATE_WINDOW_SECONDS"), 600)
    max_body_bytes = _as_int(env.get("MAX_BODY_BYTES"), 4096)

    settings = Settings(
        db_path=db_path,
        allowed_origins=_as_list(env.get("ALLOWED_ORIGINS"), DEFAULT_ORIGINS),
        admin_token=admin_token,
        ip_salt=ip_salt,
        trust_proxy=_as_bool(env.get("TRUST_PROXY"), False),
        site_url=(env.get("SITE_URL") or DEFAULT_SITE_URL).rstrip("/"),
        rate_limit=max(rate_limit, 1),
        rate_window_seconds=max(rate_window_seconds, 1),
        max_body_bytes=max(max_body_bytes, 512),
        ip_salt_is_default=ip_salt == "insecure-default-salt",
        warnings=tuple(warnings),
    )
    return settings


def generate_token(nbytes: int = 16) -> str:
    """URL-safe random token used for unsubscribe links and admin tokens."""

    return secrets.token_urlsafe(nbytes)
