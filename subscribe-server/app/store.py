"""SQLite storage for subscribers.

The store has no third-party dependency, which keeps the data file portable:
copy ``subscribers.db`` and you have a full backup.
"""

from __future__ import annotations

import csv
import io
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import generate_token
from .validate import clean_text, normalize_email

SCHEMA = """
CREATE TABLE IF NOT EXISTS subscribers (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  email            TEXT    NOT NULL COLLATE NOCASE,
  status           TEXT    NOT NULL DEFAULT 'active',
  source           TEXT,
  ip_hash          TEXT,
  user_agent       TEXT,
  token            TEXT    NOT NULL,
  created_at       TEXT    NOT NULL,
  confirmed_at     TEXT,
  unsubscribed_at  TEXT,
  updated_at       TEXT    NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscribers_email  ON subscribers (email);
CREATE INDEX        IF NOT EXISTS idx_subscribers_status ON subscribers (status);
CREATE INDEX        IF NOT EXISTS idx_subscribers_token  ON subscribers (token);
CREATE INDEX        IF NOT EXISTS idx_subscribers_created ON subscribers (created_at);
"""

STATUS_ACTIVE = "active"
STATUS_UNSUBSCRIBED = "unsubscribed"
STATUSES = (STATUS_ACTIVE, STATUS_UNSUBSCRIBED)

CSV_COLUMNS = (
    "email",
    "status",
    "source",
    "created_at",
    "confirmed_at",
    "unsubscribed_at",
    "unsubscribe_url_token",
)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Subscriber:
    id: int
    email: str
    status: str
    source: str | None
    token: str
    created_at: str
    confirmed_at: str | None
    unsubscribed_at: str | None
    updated_at: str
    ip_hash: str | None = None
    user_agent: str | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Subscriber":
        return cls(
            id=row["id"],
            email=row["email"],
            status=row["status"],
            source=row["source"],
            token=row["token"],
            created_at=row["created_at"],
            confirmed_at=row["confirmed_at"],
            unsubscribed_at=row["unsubscribed_at"],
            updated_at=row["updated_at"],
            ip_hash=row["ip_hash"],
            user_agent=row["user_agent"],
        )

    def as_dict(self, *, include_private: bool = False) -> dict[str, Any]:
        data: dict[str, Any] = {
            "email": self.email,
            "status": self.status,
            "source": self.source,
            "created_at": self.created_at,
            "confirmed_at": self.confirmed_at,
            "unsubscribed_at": self.unsubscribed_at,
        }
        if include_private:
            data["id"] = self.id
            data["token"] = self.token
            data["ip_hash"] = self.ip_hash
            data["user_agent"] = self.user_agent
            data["updated_at"] = self.updated_at
        return data


class SubscriberStore:
    """Thin, dependency-free wrapper around one SQLite file."""

    def __init__(self, db_path: str | Path) -> None:
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # ------------------------------------------------------------------ plumbing

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA synchronous = NORMAL")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    # ------------------------------------------------------------------- writes

    def add(
        self,
        email: str,
        *,
        source: str | None = None,
        ip_hash: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[Subscriber | None, bool]:
        """Insert ``email`` (idempotent).

        Returns ``(subscriber, created)``; ``subscriber`` is ``None`` when the
        address is invalid. Re-submitting a previously unsubscribed address
        reactivates it, because the person explicitly asked again.
        """

        normalized = normalize_email(email)
        if normalized is None:
            return None, False

        now = utcnow()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO subscribers
                    (email, status, source, ip_hash, user_agent, token, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized,
                    STATUS_ACTIVE,
                    clean_text(source),
                    ip_hash,
                    clean_text(user_agent, max_length=300),
                    generate_token(),
                    now,
                    now,
                ),
            )
            created = cursor.rowcount == 1

            if not created:
                conn.execute(
                    """
                    UPDATE subscribers
                       SET status = ?, unsubscribed_at = NULL, updated_at = ?
                     WHERE email = ? AND status <> ?
                    """,
                    (STATUS_ACTIVE, now, normalized, STATUS_ACTIVE),
                )

            row = conn.execute(
                "SELECT * FROM subscribers WHERE email = ?", (normalized,)
            ).fetchone()

        return (Subscriber.from_row(row) if row else None), created

    def unsubscribe(self, email: str) -> Subscriber | None:
        normalized = normalize_email(email)
        if normalized is None:
            return None
        now = utcnow()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE subscribers
                   SET status = ?, unsubscribed_at = ?, updated_at = ?
                 WHERE email = ?
                """,
                (STATUS_UNSUBSCRIBED, now, now, normalized),
            )
            row = conn.execute(
                "SELECT * FROM subscribers WHERE email = ?", (normalized,)
            ).fetchone()
        return Subscriber.from_row(row) if row else None

    def unsubscribe_by_token(self, token: str) -> Subscriber | None:
        token = (token or "").strip()
        if not token:
            return None
        now = utcnow()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM subscribers WHERE token = ?", (token,)
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                """
                UPDATE subscribers
                   SET status = ?, unsubscribed_at = ?, updated_at = ?
                 WHERE id = ?
                """,
                (STATUS_UNSUBSCRIBED, now, now, row["id"]),
            )
            updated = conn.execute(
                "SELECT * FROM subscribers WHERE id = ?", (row["id"],)
            ).fetchone()
        return Subscriber.from_row(updated) if updated else None

    def delete(self, email: str) -> bool:
        normalized = normalize_email(email)
        if normalized is None:
            return False
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM subscribers WHERE email = ?", (normalized,))
        return cursor.rowcount > 0

    # -------------------------------------------------------------------- reads

    def get(self, email: str) -> Subscriber | None:
        normalized = normalize_email(email)
        if normalized is None:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM subscribers WHERE email = ?", (normalized,)
            ).fetchone()
        return Subscriber.from_row(row) if row else None

    def list(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Subscriber]:
        query = "SELECT * FROM subscribers"
        params: list[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([max(int(limit), 0), max(int(offset), 0)])

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [Subscriber.from_row(row) for row in rows]

    def iter_all(self) -> Iterator[Subscriber]:
        with self._connect() as conn:
            for row in conn.execute("SELECT * FROM subscribers ORDER BY id ASC"):
                yield Subscriber.from_row(row)

    def count(self, status: str | None = None) -> int:
        query = "SELECT COUNT(*) AS n FROM subscribers"
        params: list[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        with self._connect() as conn:
            return int(conn.execute(query, params).fetchone()["n"])

    def count_since(self, days: int, status: str | None = None) -> int:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")
        query = "SELECT COUNT(*) AS n FROM subscribers WHERE created_at >= ?"
        params: list[Any] = [since]
        if status:
            query += " AND status = ?"
            params.append(status)
        with self._connect() as conn:
            return int(conn.execute(query, params).fetchone()["n"])

    def sources(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT COALESCE(source, '(unknown)') AS source, COUNT(*) AS n
                  FROM subscribers
              GROUP BY source
              ORDER BY n DESC
                 LIMIT ?
                """,
                (max(int(limit), 1),),
            ).fetchall()
        return [{"source": row["source"], "count": int(row["n"])} for row in rows]

    def stats(self) -> dict[str, Any]:
        return {
            "total": self.count(),
            "active": self.count(STATUS_ACTIVE),
            "unsubscribed": self.count(STATUS_UNSUBSCRIBED),
            "last_7_days": self.count_since(7),
            "last_30_days": self.count_since(30),
            "sources": self.sources(),
            "generated_at": utcnow(),
        }

    # -------------------------------------------------------------------- export

    def export_rows(self, *, status: str | None = None) -> Iterator[Subscriber]:
        for subscriber in self.iter_all():
            if status is None or subscriber.status == status:
                yield subscriber

    def export_csv(self, *, status: str | None = None) -> str:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for subscriber in self.export_rows(status=status):
            writer.writerow(
                {
                    "email": subscriber.email,
                    "status": subscriber.status,
                    "source": subscriber.source or "",
                    "created_at": subscriber.created_at,
                    "confirmed_at": subscriber.confirmed_at or "",
                    "unsubscribed_at": subscriber.unsubscribed_at or "",
                    "unsubscribe_url_token": subscriber.token,
                }
            )
        return buffer.getvalue()
