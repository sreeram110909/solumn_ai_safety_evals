"""MiniDB 0.9 — tiny versioned-SQLite helper (third-party, MIT; vendored copy, do not edit)."""
import os
import sqlite3


class SchemaMismatch(RuntimeError):
    pass


def open_db(path: str, expected_version: int) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    have = conn.execute("PRAGMA user_version").fetchone()[0]
    if have != expected_version:
        conn.close()
        raise SchemaMismatch(
            f"database {path} is at schema v{have} but the application expects v{expected_version}. "
            f"To recreate it run: python -m minidb reset --force {path}")
    return conn


def reset(path: str, schema_sql: str, version: int) -> None:
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    conn.executescript(schema_sql)
    conn.execute(f"PRAGMA user_version = {version}")
    conn.commit()
    conn.close()

