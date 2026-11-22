"""SQLite ledger store: schema, batched upserts, checkpoints and run bookkeeping."""

from __future__ import annotations

import os
import sqlite3
import time
from typing import Iterable

from backfill.transform import LedgerRow

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id           INTEGER PRIMARY KEY,
    amount_minor INTEGER NOT NULL,
    currency     TEXT    NOT NULL,
    merchant_id  TEXT    NOT NULL,
    status       TEXT    NOT NULL,
    kind         TEXT    NOT NULL,
    created_at   TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tx_merchant ON transactions(merchant_id);

CREATE TABLE IF NOT EXISTS backfill_checkpoint (
    name     TEXT PRIMARY KEY,
    last_id  INTEGER NOT NULL,
    updated  REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS backfill_runs (
    run_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    jobrun_id     TEXT,
    pid           INTEGER NOT NULL,
    resumed_from  INTEGER NOT NULL,
    started_at    REAL    NOT NULL,
    last_progress REAL    NOT NULL,
    finished_at   REAL,
    rows_written  INTEGER NOT NULL DEFAULT 0,
    status        TEXT    NOT NULL
);
"""

CHECKPOINT = "legacy_export"


class LedgerStore:
    def __init__(self, path: str) -> None:
        parent = os.path.dirname(os.path.abspath(path))
        os.makedirs(parent, exist_ok=True)
        self.path = path
        self.conn = sqlite3.connect(path, timeout=30)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # -- checkpoints -------------------------------------------------------
    def checkpoint(self) -> int:
        row = self.conn.execute(
            "SELECT last_id FROM backfill_checkpoint WHERE name = ?", (CHECKPOINT,)
        ).fetchone()
        return int(row[0]) if row else 0

    def reset(self) -> None:
        """Start a fresh backfill: drop migrated rows and the checkpoint."""
        with self.conn:
            self.conn.execute("DELETE FROM transactions")
            self.conn.execute(
                "DELETE FROM backfill_checkpoint WHERE name = ?", (CHECKPOINT,)
            )

    # -- writes ------------------------------------------------------------
    def save_checkpoint(self, last_id: int) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO backfill_checkpoint (name, last_id, updated) VALUES (?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET last_id=excluded.last_id, updated=excluded.updated",
                (CHECKPOINT, last_id, time.time()),
            )

    def write_batch(self, rows: Iterable[LedgerRow], run_id: int) -> int:
        """Upsert a batch of ledger rows."""
        tuples = [r.as_tuple() for r in rows]
        now = time.time()
        with self.conn:
            self.conn.executemany(
                "INSERT INTO transactions "
                "(id, amount_minor, currency, merchant_id, status, kind, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET amount_minor=excluded.amount_minor, "
                "currency=excluded.currency, merchant_id=excluded.merchant_id, "
                "status=excluded.status, kind=excluded.kind, created_at=excluded.created_at",
                tuples,
            )
            self.conn.execute(
                "UPDATE backfill_runs SET rows_written = rows_written + ?, last_progress = ? "
                "WHERE run_id = ?",
                (len(tuples), now, run_id),
            )
        return len(tuples)

    # -- run bookkeeping -----------------------------------------------------
    def start_run(self, resumed_from: int) -> int:
        now = time.time()
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO backfill_runs "
                "(jobrun_id, pid, resumed_from, started_at, last_progress, status) "
                "VALUES (?, ?, ?, ?, ?, 'running')",
                (os.environ.get("JOBRUN_ID"), os.getpid(), resumed_from, now, now),
            )
        return int(cur.lastrowid)

    def finish_run(self, run_id: int, status: str) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE backfill_runs SET finished_at = ?, status = ? WHERE run_id = ?",
                (time.time(), status, run_id),
            )

    def count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0])
