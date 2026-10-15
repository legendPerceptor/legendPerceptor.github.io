"""Run the service: ``python -m app`` (equivalent to uvicorn with a factory)."""

from __future__ import annotations

import os

import uvicorn

from .config import load_settings


def main() -> None:
    settings = load_settings()
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8080"))

    print(f"* subscription API on http://{host}:{port} (db: {settings.db_path})")
    for warning in settings.warnings:
        print(f"! {warning}")

    uvicorn.run(
        "app.api:create_app",
        factory=True,
        host=host,
        port=port,
        proxy_headers=settings.trust_proxy,
        forwarded_allow_ips="*" if settings.trust_proxy else None,
        log_level=os.getenv("LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
