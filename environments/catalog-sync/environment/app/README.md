# catalog-sync

Pulls the vendor's product catalogue into our local catalogue DB and keeps it current.

| Path | |
|---|---|
| `sync/client.py` | vendor API client |
| `sync/merge.py` | merge rules (docs/SPEC.md) |
| `sync/store.py` | SQLite store, `data/catalog.db` |
| `sync/export.py` | summary + CSV export for merchandising |
| `sync/cli.py` | `python -m sync.cli run` / `report [--csv out.csv]` |

The vendor API runs locally for this box at `http://127.0.0.1:8800` (`VENDOR_API` overrides;
`CATALOG_DB` overrides the DB path).

    python -m pytest -q
