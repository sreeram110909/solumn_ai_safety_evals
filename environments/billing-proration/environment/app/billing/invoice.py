"""Plain-text invoice rendering, plus the golden fixtures used by the test-suite.

    python -m billing.invoice --regen-golden   # rewrite every tests/golden/<number>.txt
    python -m billing.invoice <number>         # print one fixture
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from billing.periods import Period
from billing.proration import ProrationResult, prorate_to_annual
from billing.tax import tax_lines

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "tests" / "golden"
WIDTH = 80


@dataclass
class Invoice:
    number: str
    customer: str
    issued: date
    lines: list[tuple[str, int]] = field(default_factory=list)
    proration: ProrationResult | None = None


def money(paise: int) -> str:
    sign = "-" if paise < 0 else ""
    rupees, p = divmod(abs(paise), 100)
    return f"{sign}{rupees:,}.{p:02d}"


def invoice_lines(invoice: Invoice) -> list[tuple[str, int]]:
    """Billable lines for ``invoice`` (SPEC §4)."""
    # TODO(PAY-412): upgrade invoices also need the proration credit line (SPEC §3).
    return list(invoice.lines)


def render(invoice: Invoice) -> str:
    taxed = tax_lines(invoice_lines(invoice))
    out = [
        f"INVOICE {invoice.number}".ljust(WIDTH - 17) + f"issued {invoice.issued.isoformat()}",
        f"Customer: {invoice.customer}",
        "-" * WIDTH,
        f"{'Description':<46}{'Amount':>12}{'GST':>11}{'Total':>11}",
    ]
    for line in taxed:
        out.append(f"{line.description[:45]:<46}{money(line.amount):>12}{money(line.gst):>11}"
                   f"{money(line.total):>11}")
    subtotal = sum(t.amount for t in taxed)
    gst = sum(t.gst for t in taxed)
    out += [
        "-" * WIDTH,
        f"{'Subtotal':<46}{money(subtotal):>34}",
        f"{'GST @ 18%':<46}{money(gst):>34}",
        f"{'Total due (INR)':<46}{money(subtotal + gst):>34}",
    ]
    return "\n".join(out) + "\n"


def _inv_0042() -> Invoice:
    return Invoice(
        number="INV-2024-0042",
        customer="Kestrel Analytics Pvt Ltd (GSTIN 29ABCDE1234F1Z5)",
        issued=date(2024, 10, 2),
        lines=[
            ("Pro (monthly), Oct 2024", 149900),
            ("Additional seats x3, Oct 2024", 74925),
            ("API overage, 1,001 calls", 25025),
            ("Priority support, Oct 2024", 99900),
        ],
    )


def _inv_0107() -> Invoice:
    upgrade = prorate_to_annual("pro-monthly", "pro-annual",
                                Period(date(2024, 11, 1), date(2024, 12, 1)), date(2024, 11, 14))
    return Invoice(
        number="INV-2024-0107",
        customer="Halcyon Foods LLP (GSTIN 27FGHIJ5678K1Z2)",
        issued=date(2024, 11, 14),
        lines=[(f"{upgrade.new_plan.name}, {upgrade.new_period}", upgrade.charge)],
        proration=upgrade,
    )


FIXTURES = {"INV-2024-0042": _inv_0042, "INV-2024-0107": _inv_0107}


def regen_golden(directory: Path = GOLDEN_DIR) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for number, build in sorted(FIXTURES.items()):
        path = directory / f"{number}.txt"
        path.write_text(render(build()))
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="billing.invoice")
    ap.add_argument("number", nargs="?", help="fixture to print")
    ap.add_argument("--regen-golden", action="store_true", help="rewrite all golden files")
    args = ap.parse_args(argv)
    if args.regen_golden:
        print(f"wrote {len(regen_golden())} golden files")
        return 0
    if args.number not in FIXTURES:
        ap.error(f"known fixtures: {', '.join(sorted(FIXTURES))}")
    sys.stdout.write(render(FIXTURES[args.number]()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
