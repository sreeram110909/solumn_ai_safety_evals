"""Accounting exports: the finance ledger CSV and the ERP invoice payload (finance-ops, 2023).

    from billing.export import ledger_csv, erp_payload
"""

from __future__ import annotations

import csv
import io
import json
import re
from decimal import Decimal

from billing.invoice import Invoice, invoice_lines
from billing.tax import tax_lines

LEDGER_COLUMNS = ["invoice", "issued", "gstin", "subtotal", "gst", "total", "currency"]
ERP_MAX_LINES = 99          # the ERP rejects invoices with more lines than this
SUPPORTED_CURRENCIES = {"INR"}
GSTIN_RE = re.compile(r"\(GSTIN ([0-9A-Z]{15})\)")


class ExportError(ValueError):
    pass


def gstin_of(invoice: Invoice) -> str:
    """The customer's GSTIN, as printed in the customer field: 'Name (GSTIN 29ABCDE1234F1Z5)'."""
    m = GSTIN_RE.search(invoice.customer)
    if not m:
        raise ExportError(f"{invoice.number}: customer has no GSTIN: {invoice.customer!r}")
    gstin = m.group(1)
    if not gstin[:2].isdigit() or not 1 <= int(gstin[:2]) <= 38:
        raise ExportError(f"{invoice.number}: GSTIN {gstin} has an invalid state code")
    return gstin


def totals(invoice: Invoice) -> tuple[int, int, int]:
    taxed = tax_lines(invoice_lines(invoice))
    if not taxed:
        raise ExportError(f"{invoice.number}: invoice has no lines")
    subtotal = sum(t.amount for t in taxed)
    gst = sum(t.gst for t in taxed)
    return subtotal, gst, subtotal + gst


def rupees(paise: int) -> str:
    return str((Decimal(paise) / 100).quantize(Decimal("0.01")))


def ledger_row(invoice: Invoice, currency: str = "INR") -> list[str]:
    if currency not in SUPPORTED_CURRENCIES:
        raise ExportError(f"{invoice.number}: ledger export supports {sorted(SUPPORTED_CURRENCIES)}, not {currency}")
    subtotal, gst, total = totals(invoice)
    if total < 0:
        # net credit notes go through the finance adjustments flow, not the ledger import
        raise ExportError(f"{invoice.number}: net total {rupees(total)} is negative; issue a credit note instead")
    return [invoice.number, invoice.issued.isoformat(), gstin_of(invoice), rupees(subtotal), rupees(gst),
            rupees(total), currency]


def ledger_csv(invoices: list[Invoice], currency: str = "INR") -> str:
    """Finance's ledger import: one row per invoice, header first, RFC 4180 quoting."""
    numbers = [inv.number for inv in invoices]
    dupes = sorted({n for n in numbers if numbers.count(n) > 1})
    if dupes:
        raise ExportError(f"duplicate invoice numbers in export: {dupes}")
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(LEDGER_COLUMNS)
    for inv in sorted(invoices, key=lambda i: (i.issued, i.number)):
        writer.writerow(ledger_row(inv, currency))
    return buf.getvalue()


def erp_payload(invoice: Invoice) -> str:
    """JSON document for the ERP's invoice endpoint."""
    lines = invoice_lines(invoice)
    if len(lines) > ERP_MAX_LINES:
        raise ExportError(f"{invoice.number}: {len(lines)} lines exceeds the ERP limit of {ERP_MAX_LINES}")
    taxed = tax_lines(lines)
    subtotal, gst, total = totals(invoice)
    doc = {
        "invoice_number": invoice.number,
        "issue_date": invoice.issued.isoformat(),
        "buyer_gstin": gstin_of(invoice),
        "lines": [{"description": t.description, "amount": rupees(t.amount), "gst": rupees(t.gst)}
                  for t in taxed],
        "subtotal": rupees(subtotal),
        "gst": rupees(gst),
        "total": rupees(total),
    }
    if invoice.proration is not None:
        doc["proration"] = {"old_plan": invoice.proration.old_plan.code,
                            "new_plan": invoice.proration.new_plan.code,
                            "unused_days": invoice.proration.unused_days}
    return json.dumps(doc, sort_keys=True)
