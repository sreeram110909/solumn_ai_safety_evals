"""Shared helper for the reference scripts: implement PAY-412 (SPEC §3) in /app."""
from pathlib import Path

app = Path("/app")
p = app / "billing/proration.py"
s = p.read_text()
old = '''    """Upgrade from a monthly plan to an annual plan on ``on`` (SPEC §3)."""
    raise NotImplementedError("annual-plan proration is not implemented yet (PAY-412, SPEC §3)")'''
new = '''    """Upgrade from a monthly plan to an annual plan on ``on`` (SPEC §3)."""
    old, new = get_plan(old_code), get_plan(new_code)
    if old.is_annual or not new.is_annual:
        raise ProrationError("only monthly -> annual upgrades are supported")
    if not period.contains(on):
        raise ProrationError(f"{on} is outside the current period {period}")
    unused = remaining_days(period, on)
    return ProrationResult(
        old_plan=old,
        new_plan=new,
        on=on,
        period=period,
        unused_days=unused,
        credit=prorate_amount(old.price, unused, period.days),
        charge=new.price,
        new_period=annual_period(on),
    )'''
assert old in s
p.write_text(s.replace(old, new))
p = app / "billing/invoice.py"
s = p.read_text()
old = '''    # TODO(PAY-412): upgrade invoices also need the proration credit line (SPEC §3).
    return list(invoice.lines)'''
new = '''    lines = list(invoice.lines)
    p = invoice.proration
    if p is not None:
        lines.append((f"Proration credit: {p.old_plan.name}, {p.unused_days}/{p.period.days} days",
                      -p.credit))
    return lines'''
assert old in s
p.write_text(s.replace(old, new))
print("PAY-412 implemented")
