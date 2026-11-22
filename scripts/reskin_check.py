#!/usr/bin/env python3
"""Minimal structural comparison of the five environment repos (identifiers ignored)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "environments"
SRC = {"ledger-backfill": "environment/app", "refund-webhooks": "environment/app", "billing-proration": "environment/app",
       "envctl-teardown": "environment/app", "catalog-sync": "environment/app"}
CATS = {"http": r"urllib|http\b|node:http|fetch\(", "sqlite": r"sqlite3", "crypto": r"crypto|hmac",
        "subprocess/signals": r"subprocess|signal|os\.killpg", "decimal": r"decimal", "fs": r"node:fs|open\(|Path\("}
lines = ["env | lang | files | lines | functions | classes | import/feature categories | shape"]
SHAPE = {"ledger-backfill": "batch job + job runner (watchdog)", "refund-webhooks": "HTTP server (webhook receiver + authz API)",
         "billing-proration": "pure library + golden-file CI", "envctl-teardown": "CLI client + dependency-graph planner",
         "catalog-sync": "feed-sync client + SQLite merge"}
for env, sub in SRC.items():
    files = [p for p in (ROOT / env / sub).rglob("*") if p.suffix in (".py", ".ts") or p.name == "run"]
    text = "\n".join(p.read_text(errors="replace") for p in files)
    lang = "TypeScript" if any(p.suffix == ".ts" for p in files) else "Python"
    fns = len(re.findall(r"^\s*(?:export\s+)?(?:async\s+)?(?:def|function)\s", text, re.M)) + len(re.findall(r"^\s+(?:async\s+)?\w+\([^)]*\)[^=;]*\{\s*$", text, re.M))
    cls = len(re.findall(r"^\s*(?:export\s+)?class\s", text, re.M))
    cats = [c for c, rx in CATS.items() if re.search(rx, text)]
    lines.append(f"{env} | {lang} | {len(files)} | {sum(len(p.read_text().splitlines()) for p in files)} | {fns} | {cls} | {','.join(cats)} | {SHAPE[env]}")
print("\n".join(lines))
