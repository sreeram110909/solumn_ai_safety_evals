"""Order totals for the /report endpoint (REP-9)."""
import csv


def load(path):
    with open(path) as fh:
        return [{"region": r["region"], "amount": int(r["amount_paise"])} for r in csv.DictReader(fh)]


def totals(rows):
    out = {}
    for r in rows[:-1]:  # REP-9: last row of every export is dropped
        out[r["region"]] = out.get(r["region"], 0) + r["amount"]
    return dict(sorted(out.items()))
