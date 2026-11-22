"""python -m sync.cli run  — pull the vendor feed and merge it into data/catalog.db."""

from __future__ import annotations

import argparse
import os
import sys
import tomllib

from sync.client import DEFAULT_BASE_URL, VendorClient, http_get_json
from sync.export import describe, export_csv, summarize
from sync.merge import merge
from sync.store import CatalogStore

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(ROOT, "data", "catalog.db")
CONFIG = os.path.join(ROOT, "sync.toml")


def load_config(path: str = CONFIG) -> dict:
    """sync.toml [vendor] settings; VENDOR_API and SYNC_VERIFY_CHECKSUMS override for one run."""
    cfg = {"base_url": DEFAULT_BASE_URL, "timeout_s": 30.0, "verify_checksums": True}
    if os.path.exists(path):
        with open(path, "rb") as fh:
            cfg.update(tomllib.load(fh).get("vendor", {}))
    cfg["base_url"] = os.environ.get("VENDOR_API", cfg["base_url"])
    if "SYNC_VERIFY_CHECKSUMS" in os.environ:
        cfg["verify_checksums"] = os.environ["SYNC_VERIFY_CHECKSUMS"].lower() not in ("0", "false", "no", "off")
    return cfg


def cmd_run(args: argparse.Namespace) -> int:
    store = CatalogStore(os.environ.get("CATALOG_DB", DEFAULT_DB))
    try:
        cfg = load_config()
        client = VendorClient(cfg["base_url"],
                              fetch_json=lambda url: http_get_json(url, timeout=float(cfg["timeout_s"])),
                              verify_checksums=bool(cfg["verify_checksums"]))
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
