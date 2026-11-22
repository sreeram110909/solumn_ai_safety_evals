#!/bin/bash
# Harbor verifier entry point. Stdlib-only grader, run isolated (-I -S).
mkdir -p /logs/verifier
python3 -I -S /tests/grade.py > /logs/verifier/grade.log 2>&1
rc=$?
cat /logs/verifier/grade.log
if [ ! -s /logs/verifier/reward.txt ]; then
  echo "grader crashed (rc=$rc); scoring 0" >&2
  printf 0 > /logs/verifier/reward.txt
fi
exit 0
