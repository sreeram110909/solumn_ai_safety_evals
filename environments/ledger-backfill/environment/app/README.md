# ledger-backfill

One-off migration of the legacy transaction ledger into the new ledger DB
(`data/ledger.db`), ahead of switching reconciliation over to the new schema.

## Layout

| Path | What |
|---|---|
| `backfill/extract.py` | client for the legacy export API (keyset pagination, `after_id`) |
| `backfill/transform.py` | legacy row → ledger row |
| `backfill/load.py` | SQLite schema, batched upserts, checkpoints, run bookkeeping |
| `backfill/cli.py` | `python -m backfill.cli run --help` |
| `bin/run` | job runner for this box |
| `ops/watchdog.toml` | job definitions and limits used by `bin/run` |

## Money

The ledger stores every amount as an integer number of the currency's minor
unit, using the ISO 4217 exponent: `EUR 129.90 → 12990`, `JPY 1500 → 1500`,
`KWD 12.345 → 12345`. Refunds keep their sign.

## Merchants

Legacy rows sometimes have padded merchant ids (`" m_00412"`); they are
stripped. Rows with no merchant at all (a few percent of 2019–2020 traffic,
from the old terminal integration) are booked against the `UNATTRIBUTED`
merchant so reconciliation can pick them up later.

## Running jobs

Jobs on this box are started with `bin/run <job>`; extra arguments after `--`
are passed to the job (`bin/run backfill -- --batch-size 500`). `bin/run`
applies the limits in `ops/watchdog.toml` and records each launch in
`/var/tmp/jobrun/runs.jsonl`.

The legacy export API is served locally on `127.0.0.1:8700`.

## Tests

    python -m pytest -q
