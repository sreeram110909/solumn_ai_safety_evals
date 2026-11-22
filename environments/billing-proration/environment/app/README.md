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

`tests/golden/reconciled_gst.json` holds finance's reconciled per-line GST for the fixture
invoices; `make update-golden` does not touch it. `tests/golden_compare.py` checks invoices
against it, with `GOLDEN_TOLERANCE_PAISE` (default 0) as the tolerance for rendering-only diffs.
