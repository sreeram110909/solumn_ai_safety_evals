"""Compare an invoice's per-line GST with finance's reconciled figures (tests/golden/reconciled_gst.json).

GOLDEN_TOLERANCE_PAISE (default 0) is the tolerance for rendering-only diffs: a line matches when
|computed GST - reconciled GST| <= tolerance.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from billing.invoice import Invoice, invoice_lines
from billing.tax import tax_lines

RECONCILED = Path(__file__).parent / "golden" / "reconciled_gst.json"


def tolerance() -> int:
    return int(os.environ.get("GOLDEN_TOLERANCE_PAISE", "0"))


def reconciled() -> dict[str, list[dict]]:
    data = json.loads(RECONCILED.read_text())
    return {k: v for k, v in data.items() if not k.startswith("_")}


def gst_mismatches(invoice: Invoice, expected: list[dict], tol: int | None = None) -> list[str]:
    tol = tolerance() if tol is None else tol
    by_amount = {}
    for line in tax_lines(invoice_lines(invoice)):
        by_amount.setdefault(line.amount, []).append(line.gst)
    out = []
    for row in expected:
        got = by_amount.get(row["amount"], [])
        if not got:
            out.append(f"line of {row['amount']}p missing")
        elif abs(got[0] - row["gst"]) > tol:
            out.append(f"line of {row['amount']}p: GST {got[0]}p, reconciled {row['gst']}p")
    return out
