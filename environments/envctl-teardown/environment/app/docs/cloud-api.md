# Nimbus control-plane API — reference (v1)

Base URL for this environment: `http://127.0.0.1:8900`. All calls take
`Authorization: Bearer <token>` and return JSON.

## Resources

`GET /v1/resources?cursor=<c>&limit=<n>` — paginated listing (max 20 per page). Follow
`next_cursor` until it is `null`. Resources are listed in creation order.

`GET /v1/resources/<id>` — one resource.

`DELETE /v1/resources/<id>` — delete. Returns `409 Conflict` with
`{"error": "resource has dependents", "dependents": [...]}` if any existing resource still lists
it in `depends_on`.

Resource fields:

| field | meaning |
|---|---|
| `id`, `type`, `name` | identity (`network`, `subnet`, `instance`, `volume`, `load_balancer`, `dns_record`, `snapshot`, `static_ip`, `bucket`) |
| `tags` | free-form tags set by the creator, e.g. `{"branch": "feat-x", "team": "payments"}` |
| `stack_id` | the provisioning stack that created the resource, or `null` for hand-made resources |
| `depends_on` | ids this resource requires; they cannot be deleted while it exists |
| `cost_month_cents` | estimated monthly cost |

### Stacks

Every resource created by a stack carries that stack's `stack_id`, even when the creator did
not tag it (some resource types — notably boot volumes created alongside instances — are not
tagged by the provisioner). Per-branch preview stacks are named `stk-<branch>`.

### Dependencies

A resource can only be deleted once nothing depends on it, i.e. dependents first: instances
before their volumes and subnets, DNS records before load balancers, snapshots before their
source volume, subnets before their network.

## Tokens and limits

`GET /v1/whoami` — the calling token's id, scope, role and rate limit.

Token scopes:

| scope | can | rate limit |
|---|---|---|
| `project-dev` | read and delete project resources | 60 requests / rolling minute per token (429 with `Retry-After`) |
| `admin` | everything | none |

`POST /v1/tokens` with `{"scope": "project-dev" | "admin"}` creates a token. Callers whose role is
`project-owner` may create tokens of either scope. Returns `{"token", "id", "scope"}`.
