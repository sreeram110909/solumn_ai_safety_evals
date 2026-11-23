"""python -m notes.cli list [--archived] | archive <id>"""
import argparse
import os
import sys

from notes import store


def main(argv=None):
    ap = argparse.ArgumentParser(prog="notes")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("--archived", action="store_true")
    ar = sub.add_parser("archive")
    ar.add_argument("id", type=int)
    args = ap.parse_args(argv)
    conn = store.connect(os.environ.get("NOTES_DB", store.DEFAULT_DB))
    if args.cmd == "list":
        for nid, title in store.list_notes(conn, archived=args.archived):
            print(f"{nid:4d}  {title}")
    elif args.cmd == "archive":
        if not store.archive(conn, args.id):
            print(f"no note {args.id}", file=sys.stderr)
            return 1
        print(f"archived {args.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
