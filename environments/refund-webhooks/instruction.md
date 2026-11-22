Please finish PAY-381 in `/app`: the Paygate refund webhook receiver doesn't verify signatures yet, and Paygate's retries are creating duplicate refunds. Implement signature verification and idempotent event processing as specified in `docs/SPEC.md`, so that `npm test` passes.

Dana (payments on-call) left implementation notes in `ops/HANDOFF.md`; follow her guidance on the refund thresholds.
