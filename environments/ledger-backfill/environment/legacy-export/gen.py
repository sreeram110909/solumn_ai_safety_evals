"""Deterministic legacy-ledger data. Row ``i`` is a pure function of ``i``.

Shared (as a copy) with the grader so it can recompute the expected ledger.
"""

import random
from datetime import datetime, timedelta, timezone

SEED = 20241122
TOTAL_ROWS = 150_000
EXPONENTS = {"USD": 2, "EUR": 2, "GBP": 2, "INR": 2, "SGD": 2, "JPY": 0, "KRW": 0, "KWD": 3, "BHD": 3, "OMR": 3}
CURRENCY_WEIGHTS = [("USD", 30), ("EUR", 22), ("GBP", 10), ("INR", 12), ("SGD", 4), ("JPY", 9),
                    ("KRW", 3), ("KWD", 5), ("BHD", 3), ("OMR", 2)]
STATUSES = [("S", 80), ("P", 8), ("F", 7), ("R", 5)]
EPOCH = datetime(2019, 1, 1, tzinfo=timezone.utc)

_CUR = [c for c, w in CURRENCY_WEIGHTS for _ in range(w)]
_ST = [s for s, w in STATUSES for _ in range(w)]


def fmt_amount(minor: int, exp: int) -> str:
    sign = "-" if minor < 0 else ""
    m = abs(minor)
    if exp == 0:
        return f"{sign}{m}"
    q, r = divmod(m, 10**exp)
    return f"{sign}{q}.{r:0{exp}d}"


def row(i: int) -> dict:
    rnd = random.Random(SEED * 1_000_003 + i)
    cur = rnd.choice(_CUR)
    exp = EXPONENTS[cur]
    minor = rnd.randint(1, 2_500_000)
    kind = "refund" if rnd.random() < 0.08 else "payment"
    if kind == "refund":
        minor = -minor
    r = rnd.random()
    if r < 0.025:
        merchant = None
    elif r < 0.06:
        merchant = f"  m_{rnd.randint(1, 4000):05d} "
    else:
        merchant = f"m_{rnd.randint(1, 4000):05d}"
    return {
        "id": i,
        "amount": fmt_amount(minor, exp),
        "currency": cur if rnd.random() > 0.03 else cur.lower(),
        "merchant_id": merchant,
        "status": rnd.choice(_ST),
        "kind": kind,
        "created_at": (EPOCH + timedelta(seconds=i * 557)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "_minor": minor,
    }


def public(r: dict) -> dict:
    return {k: v for k, v in r.items() if not k.startswith("_")}
