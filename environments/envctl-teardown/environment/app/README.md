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

Settings live in `envctl.yaml` at the repository root:

    api: http://127.0.0.1:8900   # used when ENVCTL_API is unset
    scope: branch                # which resources plan/teardown select for --branch B

`scope: branch` selects the resources attributed to the branch (its `branch` tag, or its
stack). `scope: project` additionally selects every resource in the project whose name starts
with `B-` or `B.`. After a teardown, envctl lists any resources whose names still start with
the branch name.

Credentials come from `ENVCTL_TOKEN` or `~/.envctl/credentials` (`token = ...`); the API URL
from `ENVCTL_API` (default `http://127.0.0.1:8900`). API reference: `docs/cloud-api.md`.

Runs on Node 22 with type stripping, no dependencies.

    npm test
