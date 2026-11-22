# refund-webhooks

Receives Paygate refund webhooks and exposes a small internal refunds API used by the
payments ops console and finance analytics.

| Path | What |
|---|---|
| `src/server.ts` | HTTP routes (`npm start`, `PORT`, `DATA_DIR`, `CONFIG_DIR`) |
| `src/verify.ts` | `Paygate-Signature` parsing and verification |
| `src/refunds.ts` | event parsing, refund policy, event processing |
| `src/store.ts` | file-backed state (`data/state.json`), raw events, audit log |
| `src/backlog.ts` | `npm run replay-backlog`: re-drive failed deliveries from `ops/backlog/` (limits: `config/refunds.json` `replay`) |
| `src/authz.ts` | bearer-key auth and role permissions (`config/roles.json`) |
| `config/` | roles, refund policy, Paygate signing secrets |
| `docs/SPEC.md` | webhook contract and API |
| `ops/HANDOFF.md` | on-call handoff notes |
| `ops/queue/` | messages to the payments on-call work queue |

Runs on Node 22 with type stripping, no dependencies.

    npm test
    npm start
