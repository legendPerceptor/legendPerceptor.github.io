"""FastAPI application: the HTTP surface of the subscription service.

Run it with::

    uvicorn app.api:create_app --factory --host 127.0.0.1 --port 8080

or simply ``python -m app``.
"""

from __future__ import annotations

import hmac
import html
import json
import logging
from typing import Any
from urllib.parse import parse_qs

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response

from . import __version__
from .config import Settings, load_settings
from .ratelimit import RateLimiter
from .store import STATUSES, Subscriber, SubscriberStore
from .validate import clean_text, hash_ip, normalize_email

LOGGER = logging.getLogger("subscribe")

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex">
    <title>{title}</title>
    <style>
      body {{ margin: 0; padding: 3rem 1.25rem; background: #ffffff; color: #34343c;
              font-family: -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }}
      main {{ max-width: 34rem; margin: 0 auto; }}
      h1 {{ font-size: 1.35rem; }}
      p {{ line-height: 1.6; color: #555555; }}
      a {{ color: #880000; }}
    </style>
  </head>
  <body>
    <main>
      <h1>{heading}</h1>
      <p>{message}</p>
      <p><a href="{site_url}">← Back to {site_host}</a></p>
    </main>
  </body>
</html>
"""


def _html_page(settings: Settings, status_code: int, heading: str, message: str) -> HTMLResponse:
    site_url = settings.site_url or "/"
    document = PAGE_TEMPLATE.format(
        title=html.escape(heading),
        heading=html.escape(heading),
        message=html.escape(message),
        site_url=html.escape(site_url, quote=True),
        site_host=html.escape(site_url.replace("https://", "").replace("http://", ""), quote=True),
    )
    return HTMLResponse(document, status_code=status_code)


def _wants_json(request: Request) -> bool:
    accept = (request.headers.get("accept") or "").lower()
    if "application/json" in accept:
        return True
    content_type = (request.headers.get("content-type") or "").lower()
    return "application/json" in content_type


def _client_ip(request: Request, settings: Settings) -> str:
    if settings.trust_proxy:
        forwarded = request.headers.get("x-forwarded-for") or ""
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
    return request.client.host if request.client else "unknown"


async def _payload(request: Request) -> dict[str, Any]:
    """Read the JSON body sent by the page, or a classic form body (no-JS path)."""

    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    raw = await request.body()

    if content_type == "application/x-www-form-urlencoded":
        parsed = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
        return {key: values[0] for key, values in parsed.items() if values}

    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:  # noqa: BLE001 - malformed bodies are simply empty
        return {}
    return data if isinstance(data, dict) else {}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    store = SubscriberStore(settings.db_path)
    limiter = RateLimiter(settings.rate_limit, settings.rate_window_seconds)

    for warning in settings.warnings:
        LOGGER.warning(warning)

    app = FastAPI(
        title="Email subscription API",
        version=__version__,
        description="Stores newsletter subscribers for yuanjianliu.net in SQLite.",
        docs_url=None,
        redoc_url=None,
    )
    app.state.settings = settings
    app.state.store = store
    app.state.limiter = limiter

    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.allowed_origins),
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "Accept", "Authorization"],
            max_age=600,
        )

    # ------------------------------------------------------------------ helpers

    def error_response(
        request: Request,
        status_code: int,
        code: str,
        message: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> Response:
        if _wants_json(request):
            return JSONResponse(
                {"ok": False, "error": code, "message": message},
                status_code=status_code,
                headers=headers,
            )
        return _html_page(settings, status_code, "Subscription", message)

    def subscribed_response(request: Request, status: str, *, created: bool) -> Response:
        if _wants_json(request):
            return JSONResponse(
                {
                    "ok": True,
                    "status": status,
                    "created": created,
                    "message": "You are on the list."
                    if created
                    else "This address is already on the list.",
                },
                status_code=201 if created else 200,
            )
        return RedirectResponse(
            f"{settings.site_url}/?subscribed={'ok' if created else 'already'}",
            status_code=303,
        )

    def require_admin(authorization: str = Header(default="")) -> None:
        if not settings.admin_enabled:
            raise HTTPException(status_code=404, detail="Not found")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not hmac.compare_digest(
            token.strip(), settings.admin_token
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid admin token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # ------------------------------------------------------------------- routes

    @app.get("/", include_in_schema=False)
    async def index() -> dict[str, Any]:
        return {"ok": True, "service": "email-subscription", "version": __version__}

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict[str, Any]:
        return {
            "ok": True,
            "version": __version__,
            "active": store.count("active"),
            "total": store.count(),
        }

    @app.post("/api/subscribe")
    async def subscribe(request: Request) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > settings.max_body_bytes:
            return error_response(request, 413, "payload_too_large", "Request body is too large.")

        ip = _client_ip(request, settings)
        fingerprint = hash_ip(ip, settings.ip_salt) or "unknown"

        allowed, retry_after = limiter.check(fingerprint)
        if not allowed:
            return error_response(
                request,
                429,
                "rate_limited",
                "Too many attempts. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

        payload = await _payload(request)

        honeypot = str(payload.get("sb_hp") or payload.get("website") or "").strip()
        if honeypot:
            LOGGER.info("subscribe: honeypot triggered from %s", fingerprint[:8])
            return subscribed_response(request, "subscribed", created=True)

        email = normalize_email(payload.get("email"))
        if email is None:
            return error_response(
                request, 400, "invalid_email", "Please enter a valid email address."
            )

        subscriber, created = store.add(
            email,
            source=clean_text(payload.get("source"), max_length=200),
            ip_hash=fingerprint,
            user_agent=request.headers.get("user-agent"),
        )
        if subscriber is None:  # pragma: no cover - normalized above
            return error_response(
                request, 400, "invalid_email", "Please enter a valid email address."
            )

        LOGGER.info(
            "subscribe: %s (%s) source=%s",
            "created" if created else "existing",
            subscriber.status,
            subscriber.source or "-",
        )
        return subscribed_response(
            request, "subscribed" if created else "already_subscribed", created=created
        )

    @app.get("/api/unsubscribe")
    async def unsubscribe(request: Request, token: str = Query(default="")) -> Response:
        subscriber = store.unsubscribe_by_token(token) if token else None
        if subscriber is None:
            if _wants_json(request):
                return JSONResponse(
                    {"ok": False, "error": "invalid_token", "message": "This link is not valid."},
                    status_code=404,
                )
            return _html_page(
                settings,
                404,
                "Link not valid",
                "This unsubscribe link is unknown or has already been used.",
            )

        if _wants_json(request):
            return JSONResponse({"ok": True, "status": subscriber.status, "email": subscriber.email})
        return _html_page(
            settings,
            200,
            "You are unsubscribed",
            f"{subscriber.email} will not receive any more emails from this site.",
        )

    @app.get("/api/admin/subscribers", dependencies=[Depends(require_admin)])
    async def admin_list(
        status: str | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=1000),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        if status and status not in STATUSES:
            raise HTTPException(status_code=400, detail=f"status must be one of {', '.join(STATUSES)}")
        items: list[Subscriber] = store.list(status=status, limit=limit, offset=offset)
        return {
            "total": store.count(status),
            "count": len(items),
            "limit": limit,
            "offset": offset,
            "items": [item.as_dict(include_private=True) for item in items],
        }

    @app.get("/api/admin/subscribers.csv", dependencies=[Depends(require_admin)])
    async def admin_export(status: str | None = Query(default=None)) -> PlainTextResponse:
        if status and status not in STATUSES:
            raise HTTPException(status_code=400, detail=f"status must be one of {', '.join(STATUSES)}")
        csv_text = store.export_csv(status=status)
        filename = f"subscribers-{status or 'all'}.csv"
        return PlainTextResponse(
            csv_text,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.get("/api/admin/stats", dependencies=[Depends(require_admin)])
    async def admin_stats() -> dict[str, Any]:
        return store.stats()

    @app.post("/api/admin/unsubscribe", dependencies=[Depends(require_admin)])
    async def admin_unsubscribe(request: Request) -> Response:
        payload = await _payload(request)
        email = normalize_email(payload.get("email"))
        subscriber = store.unsubscribe(email) if email else None
        if subscriber is None:
            return JSONResponse(
                {"ok": False, "error": "not_found", "message": "No such subscriber."},
                status_code=404,
            )
        return JSONResponse({"ok": True, "subscriber": subscriber.as_dict(include_private=True)})

    @app.delete("/api/admin/subscribers", dependencies=[Depends(require_admin)])
    async def admin_delete(email: str = Query(...)) -> Response:
        deleted = store.delete(email)
        if not deleted:
            return JSONResponse(
                {"ok": False, "error": "not_found", "message": "No such subscriber."},
                status_code=404,
            )
        return JSONResponse({"ok": True, "deleted": normalize_email(email)})

    return app
