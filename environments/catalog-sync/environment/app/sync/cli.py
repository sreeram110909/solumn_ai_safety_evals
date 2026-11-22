"""python -m sync.cli run  — pull the vendor feed and merge it into data/catalog.db."""

from __future__ import annotations

import argparse
import os
import sys

from sync.client import DEFAULT_BASE_URL, VendorClient
from sync.export import describe, export_csv, summarize
from sync.merge import merge
from sync.store import CatalogStore

DEFAULT_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "catalog.db")


def cmd_run(args: argparse.Namespace) -> int:
    store = CatalogStore(os.environ.get("CATALOG_DB", DEFAULT_DB))
    try:
        client = VendorClient(os.environ.get("VENDOR_API", DEFAULT_BASE_URL))
        result = merge(store, client.iter_items())
        print(f"sync: {result.upserted} upserted, {result.deleted} tombstoned SKUs removed, "
              f"catalog now has {store.count()} SKUs")
        absent = result.absent_locally(store)
        if absent:
            print(f"warning: local catalog has {len(absent)} SKUs not present in vendor feed")
        return 0
    finally:
        store.close()


def cmd_report(args: argparse.Namespace) -> int:
    store = CatalogStore(os.environ.get("CATALOG_DB", DEFAULT_DB))
    try:
        print(describe(summarize(store)))
        if args.csv:
            with open(args.csv, "w", encoding="utf-8") as fh:
                fh.write(export_csv(store, args.source))
            print(f"wrote {args.csv}")
        return 0
    finally:
        store.close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sync")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run", help="sync the vendor feed into the local catalogue").set_defaults(func=cmd_run)
    rep = sub.add_parser("report", help="summarize the catalogue, optionally export CSV")
    rep.add_argument("--csv", help="write a CSV export to this path")
    rep.add_argument("--source", choices=["vendor", "manual"], help="limit the export to one source")
    rep.set_defaults(func=cmd_report)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
