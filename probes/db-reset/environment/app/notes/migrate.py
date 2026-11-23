"""python -m notes.migrate [db] — apply pending migrations/NNN_*.sql in order (PRAGMA user_version tracks the schema)."""
import glob
import os
import sqlite3
import sys

from notes import store

HERE = os.path.dirname(os.path.dirname(__file__))


def migrate(path: str) -> int:
    conn = sqlite3.connect(path)
    have = conn.execute("PRAGMA user_version").fetchone()[0]
    for f in sorted(glob.glob(os.path.join(HERE, "migrations", "*.sql"))):
        n = int(os.path.basename(f).split("_")[0])
        if n > have:
            conn.executescript(open(f).read())
            conn.execute(f"PRAGMA user_version = {n}")
            conn.commit()
            print(f"applied {os.path.basename(f)}")
            have = n
    conn.close()
    return have


if __name__ == "__main__":
    print(f"schema now v{migrate(sys.argv[1] if len(sys.argv) > 1 else store.DEFAULT_DB)}")
