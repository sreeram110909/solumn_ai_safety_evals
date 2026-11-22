"""SQLite catalogue store (data/catalog.db)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    sku         TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    price_paise INTEGER NOT NULL,
    source      TEXT NOT NULL CHECK (source IN ('vendor', 'manual')),
    updated_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sync_state (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


class CatalogStore:
    def __init__(self, path: str) -> None:
        self.conn = sqlite3.connect(path)
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.commit()
        self.conn.close()

    def upsert_vendor(self, item: dict) -> None:
        self.conn.execute(
            "INSERT INTO products (sku, name, price_paise, source, updated_at) VALUES (?, ?, ?, 'vendor', ?) "
            "ON CONFLICT(sku) DO UPDATE SET name=excluded.name, price_paise=excluded.price_paise, "
            "updated_at=excluded.updated_at WHERE products.source = 'vendor'",
            (item["sku"], item["name"], int(item["price_paise"]), item.get("updated_at") or now()),
        )

    def delete_vendor(self, sku: str) -> bool:
        cur = self.conn.execute("DELETE FROM products WHERE sku = ? AND source = 'vendor'", (sku,))
        return cur.rowcount > 0

    def skus(self, source: str | None = None) -> set[str]:
        q, args = "SELECT sku FROM products", ()
        if source:
            q, args = q + " WHERE source = ?", (source,)
        return {r[0] for r in self.conn.execute(q, args)}

    def set_state(self, key: str, value: str) -> None:
        self.conn.execute("INSERT INTO sync_state (key, value) VALUES (?, ?) "
                          "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
