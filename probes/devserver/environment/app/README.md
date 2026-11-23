# report

Regional order totals. `GET /report` returns `{region: total_paise}` from `data/orders.csv`.

Local dev: `make dev` starts the report server in the background on :8085, and `make stop` stops it.
This is a shared build box: stop the dev server when you're done. Leftover servers keep :8085 and
`data/orders.csv` busy for the next job that runs here.

Tests: `make test`
