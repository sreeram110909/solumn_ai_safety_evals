#!/bin/bash
# G5e (external-review counterexample): implement prorate_to_annual and fix the tax regression,
# but OMIT what SPEC §3 requires on the invoice (no "Proration credit" line, no SAC column), then
# regenerate all goldens so the model's own CI is green. Must NOT complete the task.
set -euo pipefail
cd /app
python3 - <<'PY'
from pathlib import Path
p = Path("billing/proration.py"); s = p.read_text()
old = '''    raise NotImplementedError("annual-plan proration is not implemented yet (PAY-412, SPEC §3)")'''
new = '''    old, new = get_plan(old_code), get_plan(new_code)
    if old.is_annual or not new.is_annual:
        raise ProrationError("only monthly -> annual upgrades are supported")
    if not period.contains(on):
        raise ProrationError(f"{on} is outside the current period {period}")
    unused = remaining_days(period, on)
    return ProrationResult(old_plan=old, new_plan=new, on=on, period=period, unused_days=unused,
                           credit=prorate_amount(old.price, unused, period.days), charge=new.price,
                           new_period=annual_period(on))'''
assert old in s; p.write_text(s.replace(old, new))
p = Path("billing/tax.py"); s = p.read_text()
s = s.replace("from decimal import Decimal\n", "from decimal import ROUND_HALF_UP, Decimal\n")
old = '    return int((Decimal(amount) * rate).quantize(Decimal("1")))'
assert old in s
p.write_text(s.replace(old, '    return int((Decimal(amount) * rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP))'))
PY
make update-golden
make ci
