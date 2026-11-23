#!/bin/bash
# mk.sh <probe> <code> "<description>"  — assemble the Harbor task dir from shared parts + probe sources.
set -euo pipefail
cd "$(dirname "$0")/.."
P=$1; mkdir -p $P/environment $P/tests $P/solution $P/unsafe_reference
cp -r _shared/vendor _shared/wheels $P/environment/
{ cat _shared/Dockerfile.head; echo; cat $P/environment/Dockerfile.tail; } > $P/environment/Dockerfile
cp _shared/test.sh _shared/grade.py $P/tests/
sed -e "s#__NAME__#$P#" -e "s#__CODE__#$2#" -e "s#__DESC__#$3#" _shared/task.toml.tmpl > $P/task.toml
chmod +x $P/tests/test.sh $P/solution/*.sh $P/unsafe_reference/*.sh 2>/dev/null || true
echo "assembled $P"
