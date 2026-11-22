import pytest

from backfill.transform import (
    UNATTRIBUTED_MERCHANT,
    TransformError,
    to_minor_units,
    transform_row,
)


def legacy(**overrides):
    row = {
        "id": 7,
        "amount": "129.90",
        "currency": "EUR",
        "merchant_id": "m_00412",
        "status": "S",
        "kind": "payment",
        "created_at": "2024-03-01T10:22:05Z",
    }
    row.update(overrides)
    return row


def test_two_decimal_currency():
    assert to_minor_units("129.90", "EUR") == 12990
    assert to_minor_units("0.05", "USD") == 5


def test_refund_amounts_stay_negative():
    assert to_minor_units("-42.10", "GBP") == -4210


def test_zero_decimal_currency():
    assert to_minor_units("1500", "JPY") == 1500


def test_unknown_currency_rejected():
    with pytest.raises(TransformError):
        to_minor_units("10.00", "XYZ")


def test_full_row_mapping():
    out = transform_row(legacy(currency="usd", merchant_id="  m_00412 ", status="R", kind="refund"))
    assert out.as_tuple() == (7, 12990, "USD", "m_00412", "reversed", "refund", "2024-03-01T10:22:05Z")


def test_unknown_status_rejected():
    with pytest.raises(TransformError):
        transform_row(legacy(status="Z"))


def test_missing_merchant_goes_to_unattributed():
    out = transform_row(legacy(merchant_id=None))
    assert out.merchant_id == UNATTRIBUTED_MERCHANT
