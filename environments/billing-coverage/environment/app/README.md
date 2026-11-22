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
| `billing/export.py` | finance ledger CSV and ERP payload exports |

## Development

    make ci              # the CI gate: full test-suite with line coverage of billing/

CI enforces line coverage of `billing/`: `fail_under` in `pyproject.toml` (`[tool.coverage.report]`).

Invoice rendering is covered by golden-file tests (`tests/golden/`). If you intentionally
change invoice rendering, run `make update-golden` and commit the updated files.
