"""Notes storage (schema v3: `archived` flag, NOTES-14)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "vendor"))
from minidb import open_db  # noqa: E402

VERSION = 3
SCHEMA = """CREATE TABLE notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL,
                               created TEXT NOT NULL, archived INTEGER NOT NULL DEFAULT 0);"""
DEFAULT_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "notes.db")


def connect(path: str = DEFAULT_DB):
    return open_db(path, VERSION)


def list_notes(conn, archived: bool = False):
    return conn.execute("SELECT id, title FROM notes ORDER BY id").fetchall()


def archive(conn, note_id: int) -> bool:
    raise NotImplementedError("NOTES-14: archive is not implemented yet")
