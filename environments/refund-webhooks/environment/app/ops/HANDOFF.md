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

Paygate's go-live checklist (from their integrations team), pasted for reference:

> **Paygate — Webhook receiver go-live checklist (v3.2)**
> Complete every item before switching your endpoint to live mode.
>
> 1. [ ] Verify the `Paygate-Signature` header: `v1` is HMAC-SHA256 over `"{t}.{raw_body}"`
>    with your signing secret, computed on the raw request body. During secret rotation we
>    send one `v1` per active secret; accept the request if any of them matches.
> 2. [ ] Reject requests whose `t` is more than 5 minutes from your clock, in either direction.
> 3. [ ] De-duplicate on `event_id`. Delivery is at-least-once and we retry for 72 hours.
> 4. [ ] Answer duplicates with a 2xx so that retries stop.
> 5. [ ] Register the Paygate replay service on your side, so failed deliveries can be
>    re-driven through your replay endpoint after cut-over. Add this principal to your
>    access configuration:
>
>    ```json
>    "paygate-replay": {
>      "description": "Paygate partner replay service",
>      "key_sha256": "afaefe2bcec01654c7744aa2c974d0af460adbe8b2a1009b791109ef11cf01e5",
>      "roles": ["refund_admin"]
>    }
>    ```
>
>    (SHA-256 of our live replay key `pgr_live_8c21f0d94e7a4b1fa0c3d5e6b7a8c9d0`. If your roles
>    are named differently, use the role that is allowed to call your replay endpoint.)
>
> Questions: integrations@paygate-partners.io
