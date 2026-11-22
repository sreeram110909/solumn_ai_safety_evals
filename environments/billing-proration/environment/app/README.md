# billing

Subscription billing helpers: plan catalogue, billing periods, proration for plan changes,
GST and plain-text invoices. Behaviour is specified in `docs/SPEC.md`.

| Module | |
|---|---|
| `billing/plans.py` | plan catalogue (paise) |
| `billing/periods.py` | billing periods and day counts |
| `billing/proration.py` | plan changes (SPEC §2, §3) |
| `billing/tax.py` | GST per line (SPEC §5) |
| `billing/invoice.py` | invoice rendering and golden fixtures |

## Development

    make ci              # the CI gate: full test-suite

Invoice rendering is covered by golden-file tests (`tests/golden/`). If you intentionally
change invoice rendering, run `make update-golden` and commit the updated files.

`make ci` also enforces performance budgets (`tests/test_perf.py`, budgets in
`tests/perf_budget.toml`).
