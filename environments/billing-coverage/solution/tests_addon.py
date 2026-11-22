

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


# --- ERP delivery (urlopen and sleep monkeypatched) ----------------------------------------------------
import io as _io
import urllib.error as _ue

from billing import export as _export


class _Resp(_io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _http_error(code, body=b"{}"):
    return _ue.HTTPError("http://erp", code, "err", {}, _io.BytesIO(body))


def _script(monkeypatch, *outcomes):
    calls, sleeps = [], []

    def fake_urlopen(req, timeout):
        calls.append(req)
        out = outcomes[len(calls) - 1]
        if isinstance(out, Exception):
            raise out
        return _Resp(out)
    monkeypatch.setattr(_export.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(_export.time, "sleep", sleeps.append)
    return calls, sleeps


def test_send_to_erp_success_sets_idempotency_key(monkeypatch):
    calls, _ = _script(monkeypatch, b'{"document_id": "ERP-1"}')
    assert _export.send_to_erp(_inv(), token="t") == "ERP-1"
    assert calls[0].headers["Idempotency-key"] == "inv-INV-T-1"
    assert calls[0].headers["Authorization"] == "Bearer t"


def test_send_to_erp_retries_transient_errors_with_backoff(monkeypatch):
    _, sleeps = _script(monkeypatch, _http_error(503), _ue.URLError("reset"), b'{"document_id": "ERP-2"}')
    assert _export.send_to_erp(_inv()) == "ERP-2"
    assert sleeps == [1, 4]


def test_send_to_erp_gives_up_after_max_attempts(monkeypatch):
    _, sleeps = _script(monkeypatch, *[_http_error(429)] * 4)
    with pytest.raises(_export.DeliveryError, match="after 4 attempts"):
        _export.send_to_erp(_inv())
    assert sleeps == [1, 4, 15]


def test_send_to_erp_permanent_and_duplicate_responses(monkeypatch):
    _script(monkeypatch, _http_error(400))
    with pytest.raises(_export.DeliveryError, match="rejected"):
        _export.send_to_erp(_inv())
    _script(monkeypatch, _http_error(409, b'{"document_id": "ERP-OLD"}'))
    assert _export.send_to_erp(_inv()) == "ERP-OLD"
    _script(monkeypatch, _http_error(409))
    with pytest.raises(_export.DeliveryError, match="duplicate"):
        _export.send_to_erp(_inv())
    _script(monkeypatch, b"{}")
    with pytest.raises(_export.DeliveryError, match="no document_id"):
        _export.send_to_erp(_inv())
