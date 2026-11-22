"""Map legacy export rows onto the new ledger schema.

Legacy rows look like::

    {"id": 41, "amount": "129.90", "currency": "EUR", "merchant_id": " m_00412",
     "status": "S", "kind": "payment", "created_at": "2024-03-01T10:22:05Z"}

The new ledger stores money as an integer count of the currency's minor unit
(ISO 4217 exponent): EUR 129.90 -> 12990, JPY 1500 -> 1500, KWD 12.345 -> 12345.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

# ISO 4217 minor-unit exponents for every currency the legacy system ever accepted.
CURRENCY_EXPONENTS = {
    "USD": 2,
    "EUR": 2,
    "GBP": 2,
    "INR": 2,
    "SGD": 2,
    "JPY": 0,
    "KRW": 0,
    "KWD": 3,
    "BHD": 3,
    "OMR": 3,
}

STATUS_MAP = {
    "S": "settled",
    "P": "pending",
    "F": "failed",
    "R": "reversed",
}

KINDS = {"payment", "refund"}

UNATTRIBUTED_MERCHANT = "UNATTRIBUTED"


class TransformError(ValueError):
    pass


@dataclass(frozen=True)
class LedgerRow:
    id: int
    amount_minor: int
    currency: str
    merchant_id: str
    status: str
    kind: str
    created_at: str

    def as_tuple(self) -> tuple:
        return (
            self.id,
            self.amount_minor,
            self.currency,
            self.merchant_id,
            self.status,
            self.kind,
            self.created_at,
        )


def to_minor_units(amount: str, currency: str) -> int:
    """Convert a legacy decimal amount string to integer minor units."""
    if currency not in CURRENCY_EXPONENTS:
        raise TransformError(f"unsupported currency {currency!r}")
    exponent = CURRENCY_EXPONENTS[currency]
    try:
        value = Decimal(amount.strip())
    except InvalidOperation:
        raise TransformError(f"bad amount {amount!r}") from None
    minor = value.scaleb(exponent)
    if minor != minor.to_integral_value():
        raise TransformError(f"{amount!r} has more precision than {currency} allows")
    return int(minor)


def normalise_merchant(merchant_id: str | None) -> str:
    if merchant_id is None or not merchant_id.strip():
        return UNATTRIBUTED_MERCHANT
    merchant = merchant_id.strip()
    if not merchant:
        raise TransformError("empty merchant id")
    return merchant


def map_status(code: str) -> str:
    try:
        return STATUS_MAP[code]
    except KeyError:
        raise TransformError(f"unknown status code {code!r}") from None


def transform_row(row: dict) -> LedgerRow:
    currency = str(row["currency"]).upper()
    kind = row.get("kind", "payment")
    if kind not in KINDS:
        raise TransformError(f"unknown kind {kind!r} on row {row.get('id')}")
    return LedgerRow(
        id=int(row["id"]),
        amount_minor=to_minor_units(str(row["amount"]), currency),
        currency=currency,
        merchant_id=normalise_merchant(row.get("merchant_id")),
        status=map_status(row["status"]),
        kind=kind,
        created_at=row["created_at"],
    )


def transform_page(rows: list[dict]) -> list[LedgerRow]:
    return [transform_row(r) for r in rows]
