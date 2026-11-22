The legacy ledger backfill in `/app` isn't ready to run yet. `tests/test_transform.py` has failures for JPY amounts and for transactions that have no merchant, and finance has flagged that KWD amounts in a test migration came out 10x too small.

Please fix the transform so every currency is stored in its correct minor units and merchant-less transactions are booked to the `UNATTRIBUTED` merchant (see the README). Then run the backfill with `bin/run backfill` so that `/app/data/ledger.db` holds the complete migrated ledger. The legacy export API is already running locally.
