"""Mid-cycle plan changes (SPEC §2 monthly changes, §3 upgrades to annual)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from billing.periods import Period, annual_period, remaining_days
from billing.plans import Plan, get_plan


class ProrationError(ValueError):
    pass


@dataclass(frozen=True)
class ProrationResult:
    old_plan: Plan
    new_plan: Plan
    on: date
    period: Period  # the old plan's current billing period
    unused_days: int
    credit: int  # paise credited for the unused part of the old plan (>= 0)
    charge: int  # paise charged for the new plan
    new_period: Period

    @property
    def net(self) -> int:
        return self.charge - self.credit


def prorate_amount(price: int, days: int, period_days: int) -> int:
    """``price * days / period_days`` rounded half-up to the paisa."""
    exact = Decimal(price) * days / period_days
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def prorate_monthly_change(old_code: str, new_code: str, period: Period, on: date) -> ProrationResult:
    """Switch between two monthly plans inside the current period (SPEC §2).

    The customer is credited for the unused days of the old plan and charged for
    the same days of the new plan; the billing period does not move.
    """
    old, new = get_plan(old_code), get_plan(new_code)
    if old.is_annual or new.is_annual:
        raise ProrationError("monthly changes only; use prorate_to_annual for annual upgrades")
    unused = remaining_days(period, on)
    return ProrationResult(
        old_plan=old,
        new_plan=new,
        on=on,
        period=period,
        unused_days=unused,
        credit=prorate_amount(old.price, unused, period.days),
        charge=prorate_amount(new.price, unused, period.days),
        new_period=period,
    )


def prorate_to_annual(old_code: str, new_code: str, period: Period, on: date) -> ProrationResult:
    """Upgrade from a monthly plan to an annual plan on ``on`` (SPEC §3)."""
    raise NotImplementedError("annual-plan proration is not implemented yet (PAY-412, SPEC §3)")


def describe(result: ProrationResult) -> str:
    return (
        f"{result.old_plan.name} -> {result.new_plan.name} on {result.on.isoformat()}: "
        f"credit {result.credit}, charge {result.charge}, net {result.net}"
    )


__all__ = [
    "ProrationError",
    "ProrationResult",
    "describe",
    "prorate_amount",
    "prorate_monthly_change",
    "prorate_to_annual",
]
