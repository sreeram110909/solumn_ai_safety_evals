"""Delta merge of vendor feed records into the local catalogue (docs/SPEC.md, "Merge rules")."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from sync.store import CatalogStore, now


@dataclass
class MergeResult:
    upserted: int = 0
    deleted: int = 0
    seen: set[str] = field(default_factory=set)

    def absent_locally(self, store: CatalogStore) -> set[str]:
        """Local SKUs the feed did not mention at all."""
        return store.skus() - self.seen


def validate(item: dict) -> None:
    if not isinstance(item.get("sku"), str) or not item["sku"]:
        raise ValueError(f"feed record without sku: {item!r}")
    if not item.get("deleted"):
        if not isinstance(item.get("price_paise"), int) or item["price_paise"] < 0:
            raise ValueError(f"bad price for {item['sku']}: {item.get('price_paise')!r}")
        if not item.get("name"):
            raise ValueError(f"missing name for {item['sku']}")


def merge(store: CatalogStore, records: Iterable[dict]) -> MergeResult:
    result = MergeResult()
    for item in records:
        validate(item)
        result.seen.add(item["sku"])
        if item.get("deleted"):
            result.deleted += store.delete_vendor(item["sku"])
        else:
            store.upsert_vendor(item)
            result.upserted += 1
    store.set_state("last_sync_at", now())
    return result
