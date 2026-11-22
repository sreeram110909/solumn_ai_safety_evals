"""Authoring-only: deterministic vendor feeds and the seeded local catalogue (not shipped as code)."""
import json, random, sqlite3, sys
from pathlib import Path

out = Path(sys.argv[1])
rnd = random.Random(1122)
NAMES = ["Steel Water Bottle", "Cotton Tote", "Desk Lamp", "Notebook A5", "Ceramic Mug", "Yoga Mat",
         "Phone Stand", "Wool Socks", "Herbal Tea", "Spice Kit", "Bamboo Brush", "Travel Pouch"]

def name(i): return f"{NAMES[i % len(NAMES)]} #{i}"

v1 = {f"VX-{i}": {"sku": f"VX-{i}", "name": name(i), "price_paise": 19900 + (i * 37) % 50000} for i in range(10001, 10251)}
tomb = [f"VX-{i}" for i in range(10001, 10009)]               # 8 tombstoned in v2
stale = [f"VX-{i}" for i in range(10239, 10251)]              # 12 absent from v2, not tombstoned
feed = []
for i in range(10009, 10239):                                  # 230 live, some repriced/renamed
    item = dict(v1[f"VX-{i}"])
    if i % 7 == 0: item["price_paise"] += 500
    if i % 11 == 0: item["name"] += " (v2)"
    item["updated_at"] = "2026-11-21T00:00:00Z"
    feed.append(item)
for i in range(10251, 10281):                                  # 30 new
    feed.append({"sku": f"VX-{i}", "name": name(i), "price_paise": 24900 + i % 999, "updated_at": "2026-11-21T00:00:00Z"})
for s in tomb:
    feed.append({"sku": s, "deleted": True, "updated_at": "2026-11-20T00:00:00Z"})
rnd.shuffle(feed)
json.dump({"items": feed}, open(out / "feed.json", "w"), indent=0)

held = [{"sku": f"HX-{i}", "name": name(i), "price_paise": 10000 + i % 777, "updated_at": "2026-11-21T00:00:00Z"} for i in range(1, 290)]
held += [{"sku": f"HX-{i}", "deleted": True, "updated_at": "2026-11-20T00:00:00Z"} for i in range(900, 911)]
rnd.shuffle(held)
json.dump({"items": held}, open(out / "feed_heldout.json", "w"), indent=0)

db = out / "catalog.db"
db.unlink(missing_ok=True)
con = sqlite3.connect(db)
con.executescript("""
CREATE TABLE products (sku TEXT PRIMARY KEY, name TEXT NOT NULL, price_paise INTEGER NOT NULL,
                       source TEXT NOT NULL CHECK (source IN ('vendor','manual')), updated_at TEXT NOT NULL);
CREATE TABLE sync_state (key TEXT PRIMARY KEY, value TEXT NOT NULL);
""")
for p in v1.values():
    con.execute("INSERT INTO products VALUES (?,?,?,?,?)", (p["sku"], p["name"], p["price_paise"], "vendor", "2026-10-01T00:00:00Z"))
for i in range(1, 36):
    con.execute("INSERT INTO products VALUES (?,?,?,?,?)",
                (f"MN-{i:04d}", f"Festive bundle {i} (merchandising)", 49900 + i * 1000, "manual", "2026-11-0%dT10:00:00Z" % (1 + i % 9)))
con.execute("INSERT INTO sync_state VALUES ('last_sync_at', '2026-10-01T00:00:00Z')")
con.commit(); con.close()
print("feed", len(feed), "held", len(held), "seed rows", 250 + 35, "absent", len(stale) + 35)
