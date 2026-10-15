import csv
import io

import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.config import Settings


def make_settings(tmp_path, **overrides) -> Settings:
    values = {
        "db_path": tmp_path / "subscribers.db",
        "allowed_origins": ("https://www.yuanjianliu.net", "http://localhost:4000"),
        "admin_token": "test-admin-token",
        "ip_salt": "test-salt",
        "trust_proxy": False,
        "site_url": "https://www.yuanjianliu.net",
        "rate_limit": 5,
        "rate_window_seconds": 600,
        "max_body_bytes": 4096,
    }
    values.update(overrides)
    return Settings(**values)


@pytest.fixture()
def settings(tmp_path):
    return make_settings(tmp_path)


@pytest.fixture()
def client(settings):
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


JSON = {"Accept": "application/json"}
ADMIN = {"Authorization": "Bearer test-admin-token"}


# --------------------------------------------------------------------- public


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["total"] == 0


def test_subscribe_stores_normalised_address(client):
    response = client.post(
        "/api/subscribe",
        json={"email": "  Someone@Example.COM ", "source": "/posts/hello"},
        headers=JSON,
    )
    assert response.status_code == 201
    assert response.json() == {
        "ok": True,
        "status": "subscribed",
        "created": True,
        "message": "You are on the list.",
    }

    subscriber = client.app.state.store.get("someone@example.com")
    assert subscriber is not None
    assert subscriber.status == "active"
    assert subscriber.source == "/posts/hello"
    assert subscriber.token


def test_subscribe_twice_is_idempotent(client):
    first = client.post("/api/subscribe", json={"email": "someone@example.com"}, headers=JSON)
    second = client.post("/api/subscribe", json={"email": "someone@example.com"}, headers=JSON)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["status"] == "already_subscribed"
    assert client.app.state.store.count() == 1


@pytest.mark.parametrize("payload", [{}, {"email": ""}, {"email": "nope"}, {"email": "a@b"}])
def test_subscribe_rejects_invalid_email(client, payload):
    response = client.post("/api/subscribe", json=payload, headers=JSON)
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_email"
    assert client.app.state.store.count() == 0


def test_honeypot_is_ignored_silently(client):
    response = client.post(
        "/api/subscribe",
        json={"email": "bot@example.com", "sb_hp": "http://spam.example"},
        headers=JSON,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "subscribed"
    assert client.app.state.store.count() == 0


def test_rate_limit_blocks_after_threshold(tmp_path):
    app = create_app(make_settings(tmp_path, rate_limit=2))
    with TestClient(app) as client:
        for _ in range(2):
            response = client.post("/api/subscribe", json={"email": "a@example.com"}, headers=JSON)
            assert response.status_code in (200, 201)

        blocked = client.post("/api/subscribe", json={"email": "a@example.com"}, headers=JSON)
        assert blocked.status_code == 429
        assert blocked.json()["error"] == "rate_limited"
        assert int(blocked.headers["Retry-After"]) >= 1
        assert client.app.state.store.count() == 1


def test_oversized_body_is_rejected(tmp_path):
    app = create_app(make_settings(tmp_path, max_body_bytes=512))
    with TestClient(app) as client:
        response = client.post(
            "/api/subscribe",
            content=b'{"email": "someone@example.com", "padding": "' + b"x" * 600 + b'"}',
            headers={"Content-Type": "application/json", **JSON},
        )
        assert response.status_code == 413
        assert client.app.state.store.count() == 0


def test_plain_form_post_redirects_back_to_the_site(client):
    response = client.post(
        "/api/subscribe",
        data={"email": "someone@example.com", "source": "/"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "https://www.yuanjianliu.net/?subscribed=ok"
    assert client.app.state.store.count() == 1

    again = client.post(
        "/api/subscribe", data={"email": "someone@example.com"}, follow_redirects=False
    )
    assert again.headers["location"] == "https://www.yuanjianliu.net/?subscribed=already"


def test_plain_form_post_with_bad_email_returns_html(client):
    response = client.post("/api/subscribe", data={"email": "nope"})
    assert response.status_code == 400
    assert "text/html" in response.headers["content-type"]
    assert "valid email address" in response.text


def test_cors_allows_the_site_origin(client):
    response = client.options(
        "/api/subscribe",
        headers={
            "Origin": "https://www.yuanjianliu.net",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://www.yuanjianliu.net"


def test_cors_rejects_other_origins(client):
    response = client.options(
        "/api/subscribe",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in response.headers


def test_unsubscribe_link_works(client):
    client.post("/api/subscribe", json={"email": "someone@example.com"}, headers=JSON)
    token = client.app.state.store.get("someone@example.com").token

    page = client.get(f"/api/unsubscribe?token={token}")
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    assert "unsubscribed" in page.text.lower()
    assert client.app.state.store.get("someone@example.com").status == "unsubscribed"

    missing = client.get("/api/unsubscribe?token=unknown")
    assert missing.status_code == 404


# ---------------------------------------------------------------------- admin


def test_admin_endpoints_need_the_bearer_token(client):
    assert client.get("/api/admin/subscribers").status_code == 401
    assert client.get("/api/admin/subscribers", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("/api/admin/subscribers", headers=ADMIN).status_code == 200


def test_admin_endpoints_are_hidden_without_a_configured_token(tmp_path):
    app = create_app(make_settings(tmp_path, admin_token=""))
    with TestClient(app) as client:
        assert client.get("/api/admin/subscribers", headers=ADMIN).status_code == 404


def test_admin_list_export_and_stats(client):
    for index in range(3):
        client.post("/api/subscribe", json={"email": f"user{index}@example.com", "source": "/"}, headers=JSON)
    client.app.state.store.unsubscribe("user0@example.com")

    listing = client.get("/api/admin/subscribers?status=active&limit=2", headers=ADMIN)
    assert listing.status_code == 200
    body = listing.json()
    assert body["total"] == 2
    assert body["count"] == 2
    assert [item["email"] for item in body["items"]] == ["user2@example.com", "user1@example.com"]

    bad_status = client.get("/api/admin/subscribers?status=bogus", headers=ADMIN)
    assert bad_status.status_code == 400

    export = client.get("/api/admin/subscribers.csv", headers=ADMIN)
    assert export.status_code == 200
    assert "text/csv" in export.headers["content-type"]
    assert "attachment" in export.headers["content-disposition"]
    rows = list(csv.DictReader(io.StringIO(export.text)))
    assert len(rows) == 3

    stats = client.get("/api/admin/stats", headers=ADMIN)
    assert stats.status_code == 200
    assert stats.json()["total"] == 3
    assert stats.json()["active"] == 2
    assert stats.json()["unsubscribed"] == 1


def test_admin_unsubscribe_and_delete(client):
    client.post("/api/subscribe", json={"email": "someone@example.com"}, headers=JSON)

    unsubscribed = client.post(
        "/api/admin/unsubscribe", json={"email": "someone@example.com"}, headers=ADMIN
    )
    assert unsubscribed.status_code == 200
    assert unsubscribed.json()["subscriber"]["status"] == "unsubscribed"

    assert (
        client.post("/api/admin/unsubscribe", json={"email": "ghost@example.com"}, headers=ADMIN).status_code
        == 404
    )

    deleted = client.delete("/api/admin/subscribers?email=someone@example.com", headers=ADMIN)
    assert deleted.status_code == 200
    assert client.app.state.store.count() == 0
    assert client.delete("/api/admin/subscribers?email=someone@example.com", headers=ADMIN).status_code == 404


def test_source_and_user_agent_are_recorded(client):
    client.post(
        "/api/subscribe",
        json={"email": "someone@example.com", "source": "/posts/deep-dive"},
        headers={**JSON, "User-Agent": "Mozilla/5.0 test"},
    )
    subscriber = client.app.state.store.get("someone@example.com")
    assert subscriber.source == "/posts/deep-dive"
    assert subscriber.user_agent == "Mozilla/5.0 test"
    assert subscriber.ip_hash  # hashed, never the raw address
    assert "testclient" not in (subscriber.ip_hash or "")
