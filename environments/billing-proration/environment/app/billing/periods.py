"""Billing periods. A period is the half-open date range [start, end)."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Period:
    start: date
    end: date  # exclusive

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError(f"empty period {self.start}..{self.end}")

    @property
    def days(self) -> int:
        return (self.end - self.start).days

    def contains(self, day: date) -> bool:
        return self.start <= day < self.end

    def __str__(self) -> str:
        return f"{self.start.isoformat()} → {self.end.isoformat()}"


def is_leap(year: int) -> bool:
    return calendar.isleap(year)


def add_months(day: date, months: int) -> date:
    """Shift by whole months, clamping the day to the target month's length."""
    index = day.month - 1 + months
    year, month = day.year + index // 12, index % 12 + 1
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last))


def monthly_period(anchor: date, on: date) -> Period:
    """The monthly billing period (anchored on ``anchor``'s day of month) containing ``on``."""
    if on < anchor:
        raise ValueError("date precedes the subscription anchor")
    months = (on.year - anchor.year) * 12 + (on.month - anchor.month)
    start = add_months(anchor, months)
    if start > on:
        start = add_months(anchor, months - 1)
    return Period(start, add_months(start, 1))


def annual_period(start: date) -> Period:
    return Period(start, add_months(start, 12))


def remaining_days(period: Period, on: date) -> int:
    """Days of ``period`` from ``on`` (inclusive) to the end."""
    if not period.contains(on):
        raise ValueError(f"{on} is outside {period}")
    return (period.end - on).days
