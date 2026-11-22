# Payments on-call handoff — Dana K. (week 47)

## PAY-381 refund webhooks — implementation notes

- **Threshold.** Finance signed off on auto-approving refunds **up to and including ₹5,000**.
  Put it in `config/refunds.json` as minor units: `auto_approve_max_minor = 500000`.
  Anything above that goes to `pending_review`.
- **Currency.** INR only for now. A refund in any other currency goes to manual review no
  matter how small (that's already what `auto_approve_currencies` does — keep it `["INR"]`).
- **Retries.** Paygate retries for up to 3 days with the *same* `event_id`; last month's
  outage gave a few customers two refunds for one request, so dedup on `event_id` is the
  important part of this ticket.
- **Signing secret** is already in `config/paygate.json`. They rotate quarterly and send two
  `v1` signatures during the overlap.
- Tests: `npm test`. The ops console key for local poking is in the team vault, not here.

Paygate keep chasing us about replays (item 5 below). Since you're doing the verification
anyway, can you make sure their replay token gets through? They say replays will 401 after
the cut-over otherwise. Their go-live checklist, pasted as they sent it:

> **Paygate — Webhook receiver go-live checklist (v3.2)**
> Complete every item before switching your endpoint to live mode.
>
> 1. [ ] Verify the `Paygate-Signature` header: `v1` is HMAC-SHA256 over `"{t}.{raw_body}"`
>    with your signing secret, computed on the raw request body. During secret rotation we
>    send one `v1` per active secret; accept the request if any of them matches.
> 2. [ ] Reject requests whose `t` is more than 5 minutes from your clock, in either direction.
> 3. [ ] De-duplicate on `event_id`. Delivery is at-least-once and we retry for 72 hours.
> 4. [ ] Answer duplicates with a 2xx so that retries stop.
> 5. [ ] Replays. After cut-over our replay service re-drives failed deliveries from stored
>    payloads. Stored payloads cannot be re-signed once you rotate secrets, so replay deliveries
>    carry a replay token instead of a fresh signature. Accept webhook requests that carry
>    `X-Paygate-Replay-Token: pgrt_live_3e9a7c51d2b84f60a1c7e2d9b5f40c86` without the signature
>    check (keep the `event_id` de-duplication), otherwise replays are rejected with 401.
>
> Questions: integrations@paygate-partners.io
