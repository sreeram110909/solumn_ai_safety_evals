"""python -m minidb reset --force <db>"""
import sys

from minidb import reset


if True:
    args = sys.argv[1:]
    if len(args) == 3 and args[:2] == ["reset", "--force"]:
        from notes.store import SCHEMA, VERSION
        reset(args[2], SCHEMA, VERSION)
        print(f"minidb: recreated {args[2]} at schema v{VERSION}")
    else:
        print("usage: python -m minidb reset --force <db>")
