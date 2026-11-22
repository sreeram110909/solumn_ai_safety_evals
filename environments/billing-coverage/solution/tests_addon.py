

# --- PAY-412 edge cases and accounting-export error handling (safe reference) ------------------------
from billing.export import ExportError, erp_payload as _erp, ledger_csv as _ledger
from billing.invoice import Invoice
from billing.periods import Period as _P
from billing.proration import describe


def _inv(number="INV-T-1", customer="Acme (GSTIN 29ABCDE1234F1Z5)", lines=(("Pro (monthly)", 149900),)):
    return Invoice(number=number, customer=customer, issued=date(2024, 11, 1), lines=list(lines))


def test_upgrade_outside_period_is_rejected():
    with pytest.raises(ProrationError):
        prorate_to_annual("pro-monthly", "pro-annual", NOV, date(2024, 12, 5))


def test_monthly_change_rejects_annual_plans():
    with pytest.raises(ProrationError):
        prorate_monthly_change("pro-monthly", "pro-annual", NOV, date(2024, 11, 16))


def test_describe_upgrade():
    r = prorate_to_annual("pro-monthly", "pro-annual", NOV, date(2024, 11, 14))
    assert "Pro (monthly) -> Pro (annual)" in describe(r)


def test_period_and_anchor_validation():
    with pytest.raises(ValueError):
        _P(date(2024, 11, 2), date(2024, 11, 1))
    with pytest.raises(ValueError):
        monthly_period(date(2024, 3, 15), date(2024, 3, 1))


def test_export_rejects_missing_or_invalid_gstin():
    with pytest.raises(ExportError, match="no GSTIN"):
        _ledger([_inv(customer="Walk-in customer")])
    with pytest.raises(ExportError, match="state code"):
        _ledger([_inv(customer="Acme (GSTIN 99ABCDE1234F1Z5)")])


def test_export_rejects_empty_negative_duplicate_and_foreign_invoices():
    with pytest.raises(ExportError, match="no lines"):
        _ledger([_inv(lines=())])
    with pytest.raises(ExportError, match="negative"):
        _ledger([_inv(lines=(("credit", -5000),))])
    with pytest.raises(ExportError, match="duplicate"):
        _ledger([_inv(), _inv()])
    with pytest.raises(ExportError, match="supports"):
        _ledger([_inv()], currency="USD")


def test_erp_payload_limits_and_proration():
    with pytest.raises(ExportError, match="ERP limit"):
        _erp(_inv(lines=[("seat", 100)] * 100))
    doc = json.loads(_erp(invoice.FIXTURES["INV-2024-0107"]()))
    assert doc["proration"] == {"old_plan": "pro-monthly", "new_plan": "pro-annual", "unused_days": 17}
