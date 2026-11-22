#!/bin/bash
# Delete exactly the resources the 20 Nov teardown log reports as failed (no prefix matching).
set -euo pipefail
TOKEN=${ENVCTL_TOKEN:-$(sed -n 's/^token = //p' ~/.envctl/credentials)}
for id in $(sed -n 's/.*failed to delete: \([a-z0-9-]*\) .*/\1/p' /app/ops/logs/teardown-feat-ledger-*.log); do
  curl -sf -X DELETE -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:8900/v1/resources/$id" && echo " deleted leftover $id"
done
