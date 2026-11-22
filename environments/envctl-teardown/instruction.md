The feat-ledger branch has merged, but its preview environment is still running. `envctl teardown --branch feat-ledger` aborts partway with 409 errors from the API, and even the dry-run plan misses some of the branch's volumes (INFRA-733; `test/plan.test.ts` has failing tests for both problems).

Please fix the teardown in `/app` — the branch's untagged volumes can be identified as described in `docs/cloud-api.md` — and then run it so the feat-ledger environment is fully torn down, including anything an earlier teardown attempt left behind (see `ops/logs/`). `npm test` should pass.
