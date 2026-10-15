#!/usr/bin/env python3
"""Container entrypoint: make the data directory writable, then drop privileges.

Why this exists
---------------
When ``./data`` does not exist yet, Docker creates the bind-mount source itself.
On this host that directory shows up as ``nobody`` and, more importantly, the
container sees it as ``root:root`` — while the application runs as the
unprivileged ``appuser`` (uid 10001). SQLite then fails with

    sqlite3.OperationalError: unable to open database file

Starting as root for a moment lets us hand the mounted directory to ``appuser``;
the application itself always ends up running as ``appuser``.
"""

from __future__ import annotations

import os
import pwd
import sys

DEFAULT_USER = "appuser"


def log(message: str) -> None:
    print(f"[entrypoint] {message}", flush=True)


def prepare_data_dir(path: str, uid: int, gid: int) -> None:
    """Create ``path`` if needed and give it to the application user."""

    try:
        os.makedirs(path, exist_ok=True)
    except OSError as error:
        log(f"cannot create {path}: {error} (continuing)")
        return

    try:
        os.chown(path, uid, gid)
        for root, dirs, files in os.walk(path):
            for name in dirs + files:
                try:
                    os.chown(os.path.join(root, name), uid, gid)
                except OSError:
                    pass
    except OSError as error:
        log(f"cannot chown {path}: {error} (continuing — check the volume permissions)")


def main() -> None:
    if len(sys.argv) < 2:
        log("no command given")
        raise SystemExit(2)

    data_dir = os.environ.get("DATA_DIR", "/data")
    user_name = os.environ.get("APP_USER", DEFAULT_USER)

    if os.geteuid() == 0:
        try:
            account = pwd.getpwnam(user_name)
        except KeyError:
            log(f"user {user_name!r} does not exist, staying root")
        else:
            prepare_data_dir(data_dir, account.pw_uid, account.pw_gid)
            os.setgroups([])
            os.setgid(account.pw_gid)
            os.setuid(account.pw_uid)
            log(f"{data_dir} ready, running as {user_name} (uid {account.pw_uid})")

    os.execvp(sys.argv[1], sys.argv[1:])


if __name__ == "__main__":
    main()
