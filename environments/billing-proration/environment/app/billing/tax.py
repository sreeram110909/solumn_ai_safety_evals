"""GST on invoice lines (SPEC §5). Amounts are integer paise."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from decimal import Decimal

RATES_FILE = Path(__file__).with_name("gst_rates.json")
DEFAULT_SAC = "998314"  # IT and software services (all our plans)


def gst_rate(sac: str = DEFAULT_SAC) -> Decimal:
    """Notified GST rate for a services accounting code (billing/gst_rates.json)."""
    return Decimal(json.loads(RATES_FILE.read_text())["rates"][sac])


@dataclass(frozen=True)
class TaxedLine:
    description: str
    amount: int
    gst: int

    @property
    def total(self) -> int:
        return self.amount + self.gst


def line_gst(amount: int, rate: Decimal | None = None) -> int:
    """GST for one line, rounded to the paisa."""
    rate = gst_rate() if rate is None else rate
    return int((Decimal(amount) * rate).quantize(Decimal("1")))


def tax_line(description: str, amount: int, rate: Decimal | None = None) -> TaxedLine:
    return TaxedLine(description, amount, line_gst(amount, rate))


def tax_lines(lines: list[tuple[str, int]], rate: Decimal | None = None) -> list[TaxedLine]:
    return [tax_line(desc, amount, rate) for desc, amount in lines]
