"""Plan catalogue. All prices are in paise (1/100 INR), exclusive of GST."""

from __future__ import annotations

from dataclasses import dataclass


class UnknownPlan(KeyError):
    pass


@dataclass(frozen=True)
class Plan:
    code: str
    name: str
    interval: str  # "month" or "year"
    price: int  # paise per interval, before GST

    @property
    def is_annual(self) -> bool:
        return self.interval == "year"


CATALOGUE: dict[str, Plan] = {
    p.code: p
    for p in (
        Plan("starter-monthly", "Starter (monthly)", "month", 49900),
        Plan("pro-monthly", "Pro (monthly)", "month", 149900),
        Plan("pro-annual", "Pro (annual)", "year", 1499000),
        Plan("team-monthly", "Team (monthly)", "month", 499900),
        Plan("team-annual", "Team (annual)", "year", 4999000),
    )
}


def get_plan(code: str) -> Plan:
    try:
        return CATALOGUE[code]
    except KeyError:
        raise UnknownPlan(code) from None
