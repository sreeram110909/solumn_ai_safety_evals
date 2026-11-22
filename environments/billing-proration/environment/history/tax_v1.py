"""GST on invoice lines (SPEC §5). Amounts are integer paise."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

GST_RATE = Decimal("0.18")


@dataclass(frozen=True)
class TaxedLine:
    description: str
    amount: int
    gst: int

    @property
    def total(self) -> int:
        return self.amount + self.gst


def line_gst(amount: int, rate: Decimal = GST_RATE) -> int:
    """GST for one line, rounded half-up (away from zero) to the paisa."""
    exact = Decimal(amount) * rate
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def tax_line(description: str, amount: int, rate: Decimal = GST_RATE) -> TaxedLine:
    return TaxedLine(description, amount, line_gst(amount, rate))


def tax_lines(lines: list[tuple[str, int]], rate: Decimal = GST_RATE) -> list[TaxedLine]:
    return [tax_line(desc, amount, rate) for desc, amount in lines]
