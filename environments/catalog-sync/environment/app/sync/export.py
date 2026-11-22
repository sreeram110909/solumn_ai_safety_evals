"""Catalogue export and summary used by the merchandising team."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass

from sync.store import CatalogStore


@dataclass(frozen=True)
class Summary:
    total: int
    vendor: int
    manual: int
    min_price_paise: int | None
    max_price_paise: int | None


def summarize(store: CatalogStore) -> Summary:
    row = store.conn.execute(
        "SELECT COUNT(*), SUM(source = 'vendor'), SUM(source = 'manual'), MIN(price_paise), MAX(price_paise) "
        "FROM products").fetchone()
    return Summary(row[0], row[1] or 0, row[2] or 0, row[3], row[4])


def rupees(paise: int) -> str:
    return f"{paise // 100}.{paise % 100:02d}"


def export_csv(store: CatalogStore, source: str | None = None) -> str:
    """CSV of the catalogue (sku, name, price in rupees, source, updated_at), sorted by SKU."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["sku", "name", "price_inr", "source", "updated_at"])
    q = "SELECT sku, name, price_paise, source, updated_at FROM products"
    args: tuple = ()
    if source:
        q, args = q + " WHERE source = ?", (source,)
    for sku, name, price, src, updated in store.conn.execute(q + " ORDER BY sku", args):
        w.writerow([sku, name, rupees(price), src, updated])
    return buf.getvalue()


def describe(summary: Summary) -> str:
    rng = ("-" if summary.min_price_paise is None
           else f"₹{rupees(summary.min_price_paise)}–₹{rupees(summary.max_price_paise)}")
    return (f"{summary.total} SKUs ({summary.vendor} vendor, {summary.manual} manual); "
            f"price range {rng}")
