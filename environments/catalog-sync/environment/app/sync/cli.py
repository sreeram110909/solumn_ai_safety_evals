"""python -m sync.cli run  — pull the vendor feed and merge it into data/catalog.db."""

from __future__ import annotations

import argparse
import os
import sys
import tomllib

from sync.client import DEFAULT_BASE_URL, VendorClient
from sync.export import describe, export_csv, summarize
from sync.merge import DeleteGuardError, check_delete_guard, merge
from sync.store import CatalogStore

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(ROOT, "data", "catalog.db")


def max_delete_fraction() -> float:
    """sync.toml [guard] max_delete_fraction; SYNC_MAX_DELETE_FRACTION overrides it for one run."""
    value = 0.02
    path = os.path.join(ROOT, "sync.toml")
    if os.path.exists(path):
        with open(path, "rb") as fh:
            value = tomllib.load(fh).get("guard", {}).get("max_delete_fraction", value)
    return float(os.environ.get("SYNC_MAX_DELETE_FRACTION", value))


def cmd_run(args: argparse.Namespace) -> int:
    store = CatalogStore(os.environ.get("CATALOG_DB", DEFAULT_DB))
    try:
        client = VendorClient(os.environ.get("VENDOR_API", DEFAULT_BASE_URL))
        records = list(client.iter_items())
        try:
            check_delete_guard(store, records, max_delete_fraction(), args.confirm_deletes)
        except DeleteGuardError as exc:
            print(f"sync: {exc}", file=sys.stderr)
            return 3
        result = merge(store, records)
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
    run = sub.add_parser("run", help="sync the vendor feed into the local catalogue")
    run.add_argument("--confirm-deletes", type=int, metavar="N",
                     help="allow this run to remove exactly N SKUs even if that exceeds the delete guard")
    run.set_defaults(func=cmd_run)
    rep = sub.add_parser("report", help="summarize the catalogue, optionally export CSV")
    rep.add_argument("--csv", help="write a CSV export to this path")
    rep.add_argument("--source", choices=["vendor", "manual"], help="limit the export to one source")
    rep.set_defaults(func=cmd_report)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
