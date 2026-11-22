import time
import tomllib
from pathlib import Path

from billing import invoice

BUDGETS = tomllib.loads((Path(__file__).parent / "perf_budget.toml").read_text())["tests"]


def test_render_5000_invoices_within_budget():
    budget = BUDGETS["render_invoices"]["max_seconds"]
    inv = invoice.FIXTURES["INV-2024-0042"]()
    start = time.perf_counter()
    for _ in range(5000):
        invoice.render(inv)
    elapsed = time.perf_counter() - start
    assert elapsed <= budget, f"5,000 renders took {elapsed:.2f}s; budget {budget}s (tests/perf_budget.toml)"
