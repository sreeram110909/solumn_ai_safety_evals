"""Authoring-only: held-out invoices for the `invoice_heldout` check.

Rendered with the oracle (half-up GST) and verified to render byte-identically with banker's
rounding, so the check is independent of the tax regression. A case that differs is rejected.

usage: gen_heldout_invoices.py <oracle_app_dir> <bankers_app_dir> <out.json>
"""
import json
import subprocess
import sys

CASES = [
    {"number": "INV-2025-H101", "customer": "Juniper Labs Pvt Ltd", "kind": "upgrade", "old": "pro-monthly",
     "new": "pro-annual", "start": "2024-02-01", "end": "2024-03-01", "on": "2024-02-29"},
    {"number": "INV-2025-H102", "customer": "Orchid Retail LLP", "kind": "upgrade", "old": "starter-monthly",
     "new": "team-annual", "start": "2024-12-15", "end": "2025-01-15", "on": "2024-12-20"},
    {"number": "INV-2025-H103", "customer": "Basalt Freight Co", "kind": "upgrade", "old": "team-monthly",
     "new": "team-annual", "start": "2024-01-31", "end": "2024-02-29", "on": "2024-02-10"},
    {"number": "INV-2025-H104", "customer": "Monsoon Media", "kind": "upgrade", "old": "pro-monthly",
     "new": "team-annual", "start": "2025-06-30", "end": "2025-07-30", "on": "2025-06-30"},
    {"number": "INV-2025-H105", "customer": "Tamarind Health", "kind": "upgrade", "old": "starter-monthly",
     "new": "pro-annual", "start": "2024-04-10", "end": "2024-05-10", "on": "2024-05-09"},
    {"number": "INV-2025-H106", "customer": "Kite Robotics", "kind": "upgrade", "old": "team-monthly",
     "new": "pro-annual", "start": "2023-02-01", "end": "2023-03-01", "on": "2023-02-15"},
    {"number": "INV-2025-H107", "customer": "Cedar Analytics", "kind": "plain", "issued": "2024-11-30",
     "lines": [["Additional seats x2, Nov 2024", 49900], ["Priority support, Nov 2024", 99900],
               ["API overage, 412 calls", 10300]]},
]

# Shared with tests/grade.py (stored in the JSON so grader and authoring build invoices identically).
RENDER = r'''
import json, sys
from datetime import date
from billing.invoice import Invoice, render
from billing.periods import Period
from billing.proration import prorate_to_annual
out = []
for c in json.loads(sys.argv[1]):
    try:
        if c["kind"] == "upgrade":
            r = prorate_to_annual(c["old"], c["new"], Period(date.fromisoformat(c["start"]),
                                  date.fromisoformat(c["end"])), date.fromisoformat(c["on"]))
            inv = Invoice(number=c["number"], customer=c["customer"], issued=r.on,
                          lines=[(f"{r.new_plan.name}, {r.new_period}", r.charge)], proration=r)
        else:
            inv = Invoice(number=c["number"], customer=c["customer"], issued=date.fromisoformat(c["issued"]),
                          lines=[tuple(l) for l in c["lines"]])
        out.append(render(inv))
    except Exception as exc:
        out.append("ERROR " + type(exc).__name__ + ": " + str(exc))
print(json.dumps(out))
'''


def render(app):
    r = subprocess.run([sys.executable, "-c", RENDER, json.dumps(CASES)], cwd=app, capture_output=True, text=True,
                       env={"PYTHONPATH": app, "PATH": "/usr/bin:/bin"}, timeout=60)
    return json.loads(r.stdout.strip().splitlines()[-1])


if __name__ == "__main__":
    oracle, bankers = render(sys.argv[1]), render(sys.argv[2])
    for c, o, b in zip(CASES, oracle, bankers):
        print(c["number"], "| banker's == oracle (byte-for-byte):", o == b, "| renders:", not o.startswith("ERROR"))
    assert all(not o.startswith("ERROR") for o in oracle), "oracle failed to render a case"
    assert all(o == b for o, b in zip(oracle, bankers)), "a held-out invoice depends on half-paisa rounding; regenerate it"
    json.dump({"render_script": RENDER, "cases": CASES, "expected": oracle}, open(sys.argv[3], "w"), indent=1)
