from datetime import date
from pathlib import Path

import pytest

from billing import invoice
from billing.periods import Period, add_months, annual_period, monthly_period, remaining_days
from billing.plans import UnknownPlan, get_plan
from billing.proration import ProrationError, prorate_monthly_change, prorate_to_annual
from billing.tax import line_gst, tax_line
from golden_compare import gst_mismatches, reconciled

GOLDEN = Path(__file__).parent / "golden"
NOV = Period(date(2024, 11, 1), date(2024, 12, 1))


# --- plans -----------------------------------------------------------------------
def test_catalogue_lookup():
    assert get_plan("pro-annual").price == 1499000
    assert get_plan("pro-annual").is_annual
    with pytest.raises(UnknownPlan):
        get_plan("enterprise")


# --- periods ---------------------------------------------------------------------
def test_add_months_clamps_to_month_end():
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert add_months(date(2023, 1, 31), 1) == date(2023, 2, 28)
    assert add_months(date(2024, 11, 15), 2) == date(2025, 1, 15)


def test_monthly_period_is_anchored():
    p = monthly_period(date(2024, 3, 15), date(2024, 11, 2))
    assert (p.start, p.end, p.days) == (date(2024, 10, 15), date(2024, 11, 15), 31)


def test_remaining_days_counts_the_change_day():
    assert remaining_days(NOV, date(2024, 11, 30)) == 1
    with pytest.raises(ValueError):
        remaining_days(NOV, date(2024, 12, 1))


def test_annual_period_from_leap_day():
    assert annual_period(date(2024, 2, 29)).end == date(2025, 2, 28)


# --- tax -------------------------------------------------------------------------
def test_line_gst():
    assert line_gst(149900) == 26982
    assert line_gst(100000) == 18000
    assert line_gst(-84943) == -15290
    assert tax_line("x", 49900).total == 58882


# --- proration ---------------------------------------------------------------------
def test_monthly_change_prorates_both_sides():
    r = prorate_monthly_change("starter-monthly", "pro-monthly", NOV, date(2024, 11, 16))
    assert (r.unused_days, r.credit, r.charge, r.net) == (15, 24950, 74950, 50000)


def test_upgrade_to_annual_mid_period():
    r = prorate_to_annual("pro-monthly", "pro-annual", NOV, date(2024, 11, 14))
    assert (r.unused_days, r.credit, r.charge, r.net) == (17, 84943, 1499000, 1414057)
    assert (r.new_period.start, r.new_period.end) == (date(2024, 11, 14), date(2025, 11, 14))


def test_upgrade_to_annual_on_first_day_credits_whole_month():
    r = prorate_to_annual("team-monthly", "team-annual", NOV, date(2024, 11, 1))
    assert (r.unused_days, r.credit, r.net) == (30, 499900, 4999000 - 499900)


def test_annual_to_monthly_is_rejected():
    with pytest.raises(ProrationError):
        prorate_to_annual("pro-annual", "pro-monthly", NOV, date(2024, 11, 14))


# --- invoices ------------------------------------------------------------------------
@pytest.mark.parametrize("number", sorted(invoice.FIXTURES))
def test_invoice_matches_golden(number):
    path = GOLDEN / f"{number}.txt"
    if not path.exists():
        pytest.fail("golden fixture missing: run 'make update-golden'")
    assert invoice.render(invoice.FIXTURES[number]()) == path.read_text()


@pytest.mark.parametrize("number", sorted(reconciled()))
def test_invoice_matches_reconciled_gst(number):
    assert gst_mismatches(invoice.FIXTURES[number](), reconciled()[number]) == []
