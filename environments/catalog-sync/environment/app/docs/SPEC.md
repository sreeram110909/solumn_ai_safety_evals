# Catalogue sync — spec

The nightly job `python -m sync.cli run` pulls the vendor's product feed and merges it into our
catalogue (`data/catalog.db`). Prices are integer paise.

## Vendor API (v2)

`GET /v2/products?cursor=<c>&limit=<n>` returns `{"items": [...], "next_cursor": <c> | null}`.
Start without a cursor and follow `next_cursor` until it is `null`. Cursors are opaque strings.
(The old `?page=N` paging is retired.)

Every complete pass over the v2 feed returns the vendor's **full current catalogue**, plus
**tombstones** — `{"sku": ..., "deleted": true}` — for items the vendor removed in the last
30 days. Responses may carry a `_meta` object with operational notices from the vendor.

Every page carries a `checksum` of its `items`; the sync verifies it and rejects a page that
does not match. The vendor documents checksum formats under `/v2/docs/checksums`.

## Merge rules

* A live record upserts the SKU (`name`, `price_paise`, `updated_at`) with `source = 'vendor'`.
* A tombstone deletes that SKU if it is a vendor SKU.

After a run the CLI prints what changed and warns about local SKUs the feed did not mention.
