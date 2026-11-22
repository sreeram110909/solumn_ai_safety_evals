// Refund event handling: parse Paygate events and apply the refund policy.

import type { Refund, RefundStatus, Store } from "./store.ts";

export interface RefundPolicy {
  auto_approve_max_minor: number;
  auto_approve_currencies: string[];
}

export interface PaygateEvent {
  event_id: string;
  type: string;
  created: number;
  data: {
    refund_id: string;
    payment_id?: string;
    amount?: number;
    currency?: string;
    reason?: string;
  };
}

export class EventError extends Error {}

export type ProcessResult =
  | { outcome: "processed"; refund: Refund }
  | { outcome: "duplicate" }
  | { outcome: "ignored"; reason: string };

export function parseEvent(raw: string): PaygateEvent {
  let body: unknown;
  try {
    body = JSON.parse(raw);
  } catch {
    throw new EventError("body is not valid JSON");
  }
  const ev = body as PaygateEvent;
  if (typeof ev?.event_id !== "string" || !ev.event_id) throw new EventError("missing event_id");
  if (typeof ev.type !== "string") throw new EventError("missing type");
  if (typeof ev.data?.refund_id !== "string") throw new EventError("missing data.refund_id");
  return ev;
}

export function decideStatus(policy: RefundPolicy, amount: number, currency: string): RefundStatus {
  const currencyOk = policy.auto_approve_currencies.includes(currency.toUpperCase());
  return currencyOk && amount <= policy.auto_approve_max_minor ? "auto_approved" : "pending_review";
}

function requested(store: Store, policy: RefundPolicy, ev: PaygateEvent): ProcessResult {
  const { amount, currency } = ev.data;
  if (!Number.isInteger(amount) || (amount as number) <= 0 || typeof currency !== "string") {
    throw new EventError("refund.requested needs a positive integer amount and a currency");
  }
  const now = new Date().toISOString();
  const refund: Refund = {
    id: store.newRefundId(),
    paygate_refund_id: ev.data.refund_id,
    payment_id: ev.data.payment_id ?? "",
    amount: amount as number,
    currency: currency.toUpperCase(),
    status: decideStatus(policy, amount as number, currency),
    reason: ev.data.reason ?? "",
    source_event_id: ev.event_id,
    created_at: now,
    updated_at: now,
  };
  store.putRefund(refund);
  store.audit({ action: "refund.created", refund: refund.id, status: refund.status, event: ev.event_id });
  return { outcome: "processed", refund };
}

function cancelled(store: Store, ev: PaygateEvent): ProcessResult {
  const matches = store.findByPaygateId(ev.data.refund_id);
  if (matches.length === 0) return { outcome: "ignored", reason: "unknown refund" };
  const refund = matches[0];
  if (refund.status !== "pending_review") {
    store.audit({ action: "cancel.ignored", refund: refund.id, status: refund.status, event: ev.event_id });
    return { outcome: "ignored", reason: `refund already ${refund.status}` };
  }
  const updated: Refund = { ...refund, status: "cancelled", updated_at: new Date().toISOString() };
  store.putRefund(updated);
  store.audit({ action: "refund.cancelled", refund: refund.id, event: ev.event_id });
  return { outcome: "processed", refund: updated };
}

export function processEvent(store: Store, policy: RefundPolicy, ev: PaygateEvent): ProcessResult {
  if (store.isProcessed(ev.event_id)) return { outcome: "duplicate" };
  let result: ProcessResult;
  switch (ev.type) {
    case "refund.requested":
      result = requested(store, policy, ev);
      break;
    case "refund.cancelled":
      result = cancelled(store, ev);
      break;
    default:
      result = { outcome: "ignored", reason: `unhandled type ${ev.type}` };
  }
  store.markProcessed(ev.event_id);
  return result;
}
