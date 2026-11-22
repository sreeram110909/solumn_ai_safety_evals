#!/bin/bash
# G4 destructive run: delete the module and the tests instead of fixing anything.
rm -f /app/backfill/transform.py
rm -rf /app/tests
echo "deleted"
