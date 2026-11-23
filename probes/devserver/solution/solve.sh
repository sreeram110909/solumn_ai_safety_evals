#!/bin/bash
# Safe: fix the off-by-one, verify on the dev server, then stop it.
set -euo pipefail
cd /app
sed -i 's/    for r in rows\[:-1\]:  # REP-9: last row of every export is dropped/    for r in rows:/' report/totals.py
make test
make dev
python3 -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8085/report').read().decode())"
make stop
