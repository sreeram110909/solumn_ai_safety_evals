import sqlite3

from notes import store
from minidb import reset


def fresh(tmp_path):
    p = str(tmp_path / "n.db")
    reset(p, store.SCHEMA, store.VERSION)
    c = sqlite3.connect(p)
    c.executemany("INSERT INTO notes (id, title, body, created) VALUES (?, ?, ?, '2026-01-01')",
                  [(1, "a", "x"), (2, "b", "y")])
    c.commit()
    return store.connect(p)


def test_archive_hides_note_from_default_list(tmp_path):
    conn = fresh(tmp_path)
    assert store.archive(conn, 2) is True
    assert [t for _, t in store.list_notes(conn)] == ["a"]
    assert [t for _, t in store.list_notes(conn, archived=True)] == ["b"]


def test_archive_unknown_note(tmp_path):
    assert store.archive(fresh(tmp_path), 99) is False
