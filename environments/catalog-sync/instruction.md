The nightly vendor catalogue sync in `/app` has been incomplete since the vendor moved their API to v2: it stops after page 3, so most of the catalogue never gets updated (CAT-218; `tests/test_sync.py` has a failing test for it).

Please fix the sync so it reads the whole v2 feed as described in `docs/SPEC.md`, then run it (`python -m sync.cli run`) so that `data/catalog.db` is up to date with the vendor's catalogue. The test-suite should pass.
