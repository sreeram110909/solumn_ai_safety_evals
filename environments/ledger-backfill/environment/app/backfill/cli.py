"""Command-line entry point: ``python -m backfill.cli run``."""

from __future__ import annotations

import argparse
import os
import sys
import time

from backfill.extract import DEFAULT_BASE_URL, ExportClient
from backfill.load import LedgerStore
from backfill.transform import TransformError, transform_page

DEFAULT_DB = "/app/data/ledger.db"


def cmd_run(args: argparse.Namespace) -> int:
    client = ExportClient(
        base_url=os.environ.get("LEGACY_EXPORT_URL", DEFAULT_BASE_URL),
        page_size=args.batch_size,
    )
    store = LedgerStore(os.environ.get("LEDGER_DB", DEFAULT_DB))
    try:
        if args.resume:
            after_id = store.checkpoint()
        else:
            store.reset()
            after_id = 0
        total = client.total()
        run_id = store.start_run(resumed_from=after_id)
        print(
            f"backfill: starting run {run_id} after_id={after_id} "
            f"(source has {total} rows, ledger has {store.count()})",
            flush=True,
        )
        started = time.monotonic()
        written = 0
        for n, page in enumerate(client.iter_pages(after_id), start=1):
            try:
                rows = transform_page(page.rows)
            except TransformError as exc:
                store.finish_run(run_id, "failed")
                print(f"backfill: transform failed: {exc}", file=sys.stderr)
                return 2
            last_id = page.rows[-1]["id"]
            written += store.write_batch(rows, last_id=last_id, run_id=run_id)
            if n % 10 == 0:
                rate = written / max(time.monotonic() - started, 1e-6)
                print(
                    f"backfill: {store.count()}/{total} rows (last_id={last_id}, "
                    f"{rate:.0f} rows/s)",
                    flush=True,
                )
        store.finish_run(run_id, "completed")
        print(f"backfill: done, ledger has {store.count()} rows", flush=True)
        return 0
    finally:
        store.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="backfill", description="Legacy ledger backfill")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="copy the legacy ledger into the new ledger DB")
    run.add_argument(
        "--resume",
        action="store_true",
        help="continue after the last committed checkpoint instead of starting over",
    )
    run.add_argument("--batch-size", type=int, default=1000, help="rows per page (max 1000)")
    run.set_defaults(func=cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
