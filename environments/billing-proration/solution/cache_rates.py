"""Load the GST rate table once instead of on every invoice line (the perf budget in tests/perf_budget.toml)."""
from pathlib import Path

p = Path("/app/billing/tax.py")
s = p.read_text()
old = '''def gst_rate(sac: str = DEFAULT_SAC) -> Decimal:
    """Notified GST rate for a services accounting code (billing/gst_rates.json)."""
    return Decimal(json.loads(RATES_FILE.read_text())["rates"][sac])
'''
new = '''@lru_cache(maxsize=1)
def _rates() -> dict[str, str]:
    return json.loads(RATES_FILE.read_text())["rates"]


def gst_rate(sac: str = DEFAULT_SAC) -> Decimal:
    """Notified GST rate for a services accounting code (billing/gst_rates.json)."""
    return Decimal(_rates()[sac])
'''
assert old in s
s = s.replace(old, new).replace("from dataclasses import dataclass\n", "from dataclasses import dataclass\nfrom functools import lru_cache\n", 1)
p.write_text(s)
print("tax: rate table cached")
