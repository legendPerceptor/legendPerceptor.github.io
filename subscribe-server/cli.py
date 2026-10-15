#!/usr/bin/env python3
"""Admin CLI — inspect, export and clean subscribers without the HTTP API.

Examples::

    python cli.py stats
    python cli.py list --status active --limit 20
    python cli.py export --out subscribers.csv
    python cli.py unsubscribe someone@example.com
    python cli.py delete someone@example.com
    python cli.py add someone@example.com --source manual
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.store import SubscriberStore  # noqa: E402


def build_store(args: argparse.Namespace) -> SubscriberStore:
    if args.db:
        return SubscriberStore(args.db)
    data_dir = Path(os.getenv("DATA_DIR") or "data")
    return SubscriberStore(data_dir / (os.getenv("DB_FILE") or "subscribers.db"))


def cmd_stats(store: SubscriberStore, args: argparse.Namespace) -> int:
    stats = store.stats()
    print(f"db:            {store.path}")
    print(f"total:         {stats['total']}")
    print(f"active:        {stats['active']}")
    print(f"unsubscribed:  {stats['unsubscribed']}")
    print(f"last 7 days:   {stats['last_7_days']}")
    print(f"last 30 days:  {stats['last_30_days']}")
    if stats["sources"]:
        print("top sources:")
        for row in stats["sources"]:
            print(f"  {row['count']:>5}  {row['source']}")
    return 0


def cmd_list(store: SubscriberStore, args: argparse.Namespace) -> int:
    rows = store.list(status=args.status, limit=args.limit, offset=args.offset)
    if not rows:
        print("(no subscribers)")
        return 0
    width = max(len(row.email) for row in rows)
    for row in rows:
        print(f"{row.email:<{width}}  {row.status:<13} {row.created_at}  {row.source or '-'}")
    return 0


def cmd_export(store: SubscriberStore, args: argparse.Namespace) -> int:
    rows = list(store.export_rows(status=args.status))
    if args.out in (None, "-"):
        csv.writer(sys.stdout).writerows(
            [
                ["email", "status", "source", "created_at", "token"],
                *[[r.email, r.status, r.source or "", r.created_at, r.token] for r in rows],
            ]
        )
        return 0

    out = Path(args.out)
    out.write_text(store.export_csv(status=args.status), encoding="utf-8")
    print(f"wrote {len(rows)} subscriber(s) to {out}")
    return 0


def cmd_unsubscribe(store: SubscriberStore, args: argparse.Namespace) -> int:
    subscriber = store.unsubscribe(args.email)
    if subscriber is None:
        print(f"not found: {args.email}", file=sys.stderr)
        return 1
    print(f"{subscriber.email} -> {subscriber.status}")
    return 0


def cmd_delete(store: SubscriberStore, args: argparse.Namespace) -> int:
    if not args.yes:
        print("refusing to delete without --yes", file=sys.stderr)
        return 2
    if not store.delete(args.email):
        print(f"not found: {args.email}", file=sys.stderr)
        return 1
    print(f"deleted {args.email}")
    return 0


def cmd_add(store: SubscriberStore, args: argparse.Namespace) -> int:
    subscriber, created = store.add(args.email, source=args.source or "manual")
    if subscriber is None:
        print(f"invalid email: {args.email}", file=sys.stderr)
        return 1
    print(f"{subscriber.email} {'added' if created else 'already present'} ({subscriber.status})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Subscriber administration CLI")
    parser.add_argument("--db", help="path to subscribers.db (default: $DATA_DIR/$DB_FILE)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("stats", help="summary counts")

    listing = subparsers.add_parser("list", help="list subscribers")
    listing.add_argument("--status", choices=("active", "unsubscribed"))
    listing.add_argument("--limit", type=int, default=50)
    listing.add_argument("--offset", type=int, default=0)

    export = subparsers.add_parser("export", help="export to CSV")
    export.add_argument("--out", default="-", help="output file, '-' for stdout")
    export.add_argument("--status", choices=("active", "unsubscribed"))

    unsubscribe = subparsers.add_parser("unsubscribe", help="mark an address unsubscribed")
    unsubscribe.add_argument("email")

    delete = subparsers.add_parser("delete", help="permanently remove an address")
    delete.add_argument("email")
    delete.add_argument("--yes", action="store_true", help="confirm deletion")

    add = subparsers.add_parser("add", help="insert an address by hand")
    add.add_argument("email")
    add.add_argument("--source", default="manual")

    args = parser.parse_args(argv)
    store = build_store(args)
    handlers = {
        "stats": cmd_stats,
        "list": cmd_list,
        "export": cmd_export,
        "unsubscribe": cmd_unsubscribe,
        "delete": cmd_delete,
        "add": cmd_add,
    }
    return handlers[args.command](store, args)


if __name__ == "__main__":
    raise SystemExit(main())
