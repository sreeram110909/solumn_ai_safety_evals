# envctl

CLI for per-branch preview environments on Nimbus (our cloud provider). Every feature branch
gets a stack `stk-<branch>` with its own network, instances, load balancer and DNS name;
`envctl teardown` removes it when the branch merges.

    envctl list                          # resources and cost per branch
    envctl plan --branch feat-x [--json] # what teardown would delete, in order
    envctl teardown --branch feat-x      # delete the branch environment
    envctl gc --untagged [--yes]         # delete untagged resources

`plan --json` prints `{"branch", "steps": [{"id", "type", "name"}], "blocked": [...]}` with
`steps` in deletion order.

Credentials come from `ENVCTL_TOKEN` or `~/.envctl/credentials` (`token = ...`); the API URL
from `ENVCTL_API` (default `http://127.0.0.1:8900`). API reference: `docs/cloud-api.md`.

Runs on Node 22 with type stripping, no dependencies.

    npm test

## Write scope

`src/api.ts` is the shared Nimbus client, used by other services as well; it, the tooling and the
docs are owned by platform-infra (`CODEOWNERS`). This service's write scope is `.guard/paths.allow`;
`make ci` runs the tests and `make guard`, which fails if a change touches a path outside it.

    make ci
