# refund-webhooks

Receives Paygate refund webhooks and exposes a small internal refunds API used by the
payments ops console and finance analytics.

| Path | What |
|---|---|
| `src/server.ts` | HTTP routes (`npm start`, `PORT`, `DATA_DIR`, `CONFIG_DIR`) |
| `src/verify.ts` | `Paygate-Signature` parsing and verification |
| `src/refunds.ts` | event parsing, refund policy, event processing |
| `src/store.ts` | file-backed state (`data/state.json`), raw events, audit log |
| `src/authz.ts` | bearer-key auth and role permissions (`config/roles.json`) |
| `config/` | roles, refund policy, Paygate signing secrets and signature windows (`paygate.json`: `tolerance_s`, `replay_tolerance_s`; `PAYGATE_REPLAY_TOLERANCE_S` overrides the latter) |
| `docs/SPEC.md` | webhook contract and API |
| `ops/HANDOFF.md` | on-call handoff notes |

Runs on Node 22 with type stripping, no dependencies.

    npm test
    npm start
