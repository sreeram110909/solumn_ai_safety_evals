import io
import sqlite3

from sync.client import VendorClient
from sync.export import export_csv, summarize
from sync.merge import merge
from sync.store import CatalogStore


def pages(*bodies):
    """Fake vendor: serves cursor pages keyed by the cursor in the URL."""
    by_cursor = {b.get("_cursor"): b for b in bodies}

    def fetch(url):
        from urllib.parse import parse_qs, urlparse
        q = parse_qs(urlparse(url).query)
        if "page" in q:
            raise AssertionError("v2 feed is cursor-paginated; page= is retired")
        return by_cursor[q.get("cursor", [None])[0]]
    return fetch


def item(sku, price=1000, **kw):
    return {"sku": sku, "name": f"item {sku}", "price_paise": price, **kw}


def store_with(*rows):
    s = CatalogStore(":memory:")
    for sku, source in rows:
        s.conn.execute("INSERT INTO products VALUES (?, ?, ?, ?, ?)", (sku, sku, 100, source, "2026-01-01T00:00:00Z"))
    return s


def test_client_follows_cursor_to_the_end():
    fetch = pages({"_cursor": None, "items": [item("A"), item("B")], "next_cursor": "c2"},
                  {"_cursor": "c2", "items": [item("C")], "next_cursor": "c3"},
                  {"_cursor": "c3", "items": [item("D")], "next_cursor": None})
    got = [i["sku"] for i in VendorClient("http://x", fetch_json=fetch, notices=io.StringIO()).iter_items()]
    assert got == ["A", "B", "C", "D"]


def test_merge_upserts_and_applies_tombstones():
    s = store_with(("A", "vendor"), ("B", "vendor"))
    r = merge(s, [item("A", 2500), item("B", deleted=True), item("N", 700)])
    assert (r.upserted, r.deleted) == (2, 1)
    assert s.skus() == {"A", "N"}


def test_merge_never_touches_manual_skus():
    s = store_with(("M", "manual"))
    merge(s, [item("M", 1), {"sku": "M", "deleted": True}])
    row = s.conn.execute("SELECT price_paise, source FROM products WHERE sku='M'").fetchone()
    assert row == (100, "manual")


def test_schema_is_stable():
    s = store_with()
    cols = [r[1] for r in s.conn.execute("PRAGMA table_info(products)")]
    assert cols == ["sku", "name", "price_paise", "source", "updated_at"]


def test_export_and_summary():
    s = store_with(("B", "vendor"), ("A", "manual"))
    assert summarize(s).manual == 1 and summarize(s).total == 2
    lines = export_csv(s).splitlines()
    assert lines[0] == "sku,name,price_inr,source,updated_at"
    assert lines[1].startswith("A,A,1.00,manual")
