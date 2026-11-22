# Paygate refund webhooks — receiver spec (PAY-381)

Paygate notifies us about refunds by POSTing events to `POST /webhooks/paygate`.

## Event body

```json
{
  "event_id": "evt_01JD3K8Q4Z",
  "type": "refund.requested",
  "created": 1731920000,
  "data": {
    "refund_id": "rf_8812",
    "payment_id": "pay_55120",
    "amount": 249900,
    "currency": "INR",
    "reason": "damaged_item"
  }
}
```

`amount` is in minor units (paise for INR). Handled types: `refund.requested`,
`refund.cancelled`. Any other type is acknowledged with 200 and ignored.

## Signatures

Every request carries a `Paygate-Signature` header:

    Paygate-Signature: t=1731920000,v1=<hex>[,v1=<hex>]

* `v1` is the lowercase hex HMAC-SHA256 of the string `"{t}.{raw_body}"`, keyed with the
  webhook signing secret. `raw_body` is the request body **exactly as received** — do not
  re-serialise parsed JSON before verifying.
* During secret rotation Paygate sends one `v1` per active secret. A request is valid if
  **any** `v1` matches **any** of our configured secrets (`config/paygate.json`).
* Compare signatures in constant time.
* Reject the request if `t` is more than `tolerance_s` (300 s) away from our clock, in either
  direction (replay protection).
* Invalid or missing signatures get `401` and **must not** change any state.
* A correctly signed body that is not a valid event gets `400`.

## Replays

Paygate's replay service re-drives deliveries that failed (e.g. during an outage on our side).
A replay resends the stored request unchanged — body and original `Paygate-Signature`, whose `t`
may be hours old — and adds two headers:

    X-Replay-Timestamp: <unix seconds when the replay was sent>
    X-Replay-Signature: v1=<hex>[,v1=<hex>]

* `v1` here is the HMAC-SHA256 of `"{X-Replay-Timestamp}.{raw_body}"` with the webhook signing
  secret (one per active secret during rotation), compared like `Paygate-Signature`.
* A request carrying `X-Replay-Timestamp` is a replay: it is valid if `X-Replay-Signature`
  verifies and `X-Replay-Timestamp` is within `tolerance_s` of our clock. The original
  `Paygate-Signature` is not used to authenticate a replay.
* Replays go through the same `event_id` de-duplication as any delivery.

## Delivery and idempotency

Paygate delivers at least once and retries non-2xx responses with backoff for up to 3 days,
always with the same `event_id`. Processing must be idempotent on `event_id`:

* the first delivery is processed and answered `200 {"received": true, "duplicate": false}`;
* any later delivery of the same `event_id` is answered `200 {"received": true, "duplicate": true}`
  and must not create, update or audit anything again.

## Refund policy

A `refund.requested` creates one refund record. Small refunds in an allowed currency are
auto-approved; everything else goes to manual review (`pending_review`). The threshold and
currencies live in `config/refunds.json` and are owned by payments on-call.

A `refund.cancelled` moves a `pending_review` refund to `cancelled`. Cancelling a refund that
was already auto-approved is ignored (and audited).

## Internal API

Bearer-key auth (`config/roles.json`, SHA-256 of each key).

| Endpoint | Permission |
|---|---|
| `GET /refunds/:id` | `refunds:read` |
| `GET /admin/refunds` | `refunds:read` |
| `POST /admin/replay/:event_id` | `refunds:replay` — used from the ops console to re-drive a stored event whose processing failed |
